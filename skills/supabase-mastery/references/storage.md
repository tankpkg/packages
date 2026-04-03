# Storage

Sources: Supabase Storage Documentation (2024-2026), Supabase Storage API GitHub (supabase/storage-api), supabase-js v2 Storage Reference, Supabase Blog (Storage v3, Image Transformations)

Covers: Bucket types and configuration, upload patterns (standard and resumable), signed URLs, public access, image transformations, storage RLS policies, CDN behavior, and S3 compatibility.

## Storage Architecture

Supabase Storage stores files in buckets backed by S3-compatible object storage. Access control uses RLS policies on the `storage.objects` and `storage.buckets` tables.

### Bucket Types

| Type | Use Case | Access Pattern |
|------|----------|---------------|
| Private (default) | User uploads, sensitive documents | Signed URLs or authenticated requests |
| Public | Profile avatars, marketing assets | Direct URL access, CDN-cached |

### Create Buckets

```sql
-- Via SQL (in migration)
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documents',
  'documents',
  false,
  10485760,  -- 10MB in bytes
  array['application/pdf', 'image/png', 'image/jpeg']
);
```

```typescript
// Via client (requires service role or appropriate policy)
const { data, error } = await supabase.storage.createBucket('avatars', {
  public: true,
  fileSizeLimit: 5242880,  // 5MB
  allowedMimeTypes: ['image/png', 'image/jpeg', 'image/webp'],
});
```

## Upload Patterns

### Standard Upload

```typescript
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.png`, file, {
    cacheControl: '3600',
    upsert: true,  // overwrite if exists
    contentType: 'image/png',
  });
```

### Upload from Browser File Input

```typescript
async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
  const file = event.target.files?.[0];
  if (!file) return;

  const fileExt = file.name.split('.').pop();
  const fileName = `${userId}/${Date.now()}.${fileExt}`;

  const { data, error } = await supabase.storage
    .from('uploads')
    .upload(fileName, file, {
      cacheControl: '3600',
      upsert: false,
    });

  if (error) {
    console.error('Upload error:', error.message);
    return;
  }

  // Get public URL (for public buckets)
  const { data: { publicUrl } } = supabase.storage
    .from('uploads')
    .getPublicUrl(data.path);
}
```

### Resumable Upload (Large Files)

For files over 6MB, use the TUS protocol for resumable uploads:

```typescript
const { data, error } = await supabase.storage
  .from('large-files')
  .upload(filePath, file, {
    // Automatically uses TUS for files > 6MB
    duplex: 'half',
  });
```

For manual TUS integration (e.g., with Uppy):

```typescript
import Uppy from '@uppy/core';
import Tus from '@uppy/tus';

const uppy = new Uppy().use(Tus, {
  endpoint: `${supabaseUrl}/storage/v1/upload/resumable`,
  headers: {
    authorization: `Bearer ${session.access_token}`,
    'x-upsert': 'true',
  },
  uploadDataDuringCreation: true,
  chunkSize: 6 * 1024 * 1024, // 6MB chunks
  metadata: {
    bucketName: 'large-files',
    objectName: fileName,
    contentType: file.type,
  },
});
```

## Accessing Files

### Public URL (Public Buckets)

```typescript
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('user-123/avatar.png');
// data.publicUrl: https://<ref>.supabase.co/storage/v1/object/public/avatars/user-123/avatar.png
```

Public URLs are served via CDN. No authentication required.

### Signed URL (Private Buckets)

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrl('user-123/contract.pdf', 3600); // expires in 1 hour
// data.signedUrl: https://<ref>.supabase.co/storage/v1/object/sign/documents/...?token=xxx
```

### Signed URLs in Bulk

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .createSignedUrls(
    ['file1.pdf', 'file2.pdf', 'file3.pdf'],
    3600
  );
```

### Download File

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .download('user-123/report.pdf');
// data is a Blob
```

## Image Transformations

Transform images on-the-fly via URL parameters. Transformed images are cached on the CDN.

### Via Client Library

```typescript
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('user-123/photo.jpg', {
    transform: {
      width: 200,
      height: 200,
      resize: 'cover',    // 'cover' | 'contain' | 'fill'
      quality: 80,         // 1-100
      format: 'origin',    // 'origin' | 'avif' | 'webp'
    },
  });
```

### Via URL Parameters

```
https://<ref>.supabase.co/storage/v1/render/image/public/avatars/photo.jpg
  ?width=200&height=200&resize=cover&quality=80
```

### Transformation Options

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `width` | 1-2500 | Original | Target width in pixels |
| `height` | 1-2500 | Original | Target height in pixels |
| `resize` | `cover`, `contain`, `fill` | `cover` | Resize mode |
| `quality` | 1-100 | 80 | Compression quality |
| `format` | `origin`, `avif`, `webp` | `origin` | Output format |

Image transformations are available on Pro plan and above.

## Storage RLS Policies

Storage uses the `storage.objects` table for RLS. The `name` column contains the file path.

### Common Policy Patterns

```sql
-- Users can upload to their own folder
create policy "users_upload_own_folder"
on storage.objects for insert
to authenticated
with check (
  bucket_id = 'avatars'
  and (select auth.uid())::text = (storage.foldername(name))[1]
);

-- Users can read their own files
create policy "users_read_own_files"
on storage.objects for select
to authenticated
using (
  bucket_id = 'avatars'
  and (select auth.uid())::text = (storage.foldername(name))[1]
);

-- Users can update/overwrite their own files
create policy "users_update_own_files"
on storage.objects for update
to authenticated
using (
  bucket_id = 'avatars'
  and (select auth.uid())::text = (storage.foldername(name))[1]
);

-- Users can delete their own files
create policy "users_delete_own_files"
on storage.objects for delete
to authenticated
using (
  bucket_id = 'avatars'
  and (select auth.uid())::text = (storage.foldername(name))[1]
);
```

### Public Read, Authenticated Upload

```sql
-- Anyone can view files in the public-assets bucket
create policy "public_read"
on storage.objects for select
to anon, authenticated
using ( bucket_id = 'public-assets' );

-- Only authenticated users can upload
create policy "authenticated_upload"
on storage.objects for insert
to authenticated
with check ( bucket_id = 'public-assets' );
```

### Storage Helper Functions

| Function | Returns | Use In Policies |
|----------|---------|----------------|
| `storage.foldername(name)` | Array of path segments | Match user folder: `(storage.foldername(name))[1]` |
| `storage.filename(name)` | File name only | Match specific files |
| `storage.extension(name)` | File extension | Restrict file types |

### Organization-Scoped Storage

```sql
create policy "org_members_access"
on storage.objects for select
to authenticated
using (
  bucket_id = 'org-files'
  and (storage.foldername(name))[1] in (
    select org_id::text from public.org_members
    where user_id = (select auth.uid())
  )
);
```

## File Management

### List Files

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .list('user-123/', {
    limit: 100,
    offset: 0,
    sortBy: { column: 'created_at', order: 'desc' },
  });
```

### Move/Rename File

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .move('old-path/file.pdf', 'new-path/file.pdf');
```

### Copy File

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .copy('source/file.pdf', 'destination/file.pdf');
```

### Delete Files

```typescript
const { data, error } = await supabase.storage
  .from('documents')
  .remove(['user-123/old-file.pdf', 'user-123/temp.pdf']);
```

## S3 Compatibility

Supabase Storage exposes an S3-compatible API for use with existing S3 tools and SDKs:

```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';

const s3 = new S3Client({
  forcePathStyle: true,
  region: 'us-east-1',
  endpoint: `https://${projectRef}.supabase.co/storage/v1/s3`,
  credentials: {
    accessKeyId: 'your-access-key',       // from Dashboard > Storage > S3 Access Keys
    secretAccessKey: 'your-secret-key',
  },
});

await s3.send(new PutObjectCommand({
  Bucket: 'avatars',
  Key: 'user-123/photo.jpg',
  Body: fileBuffer,
  ContentType: 'image/jpeg',
}));
```

## Common Mistakes

| Mistake | Risk | Fix |
|---------|------|-----|
| No RLS on storage.objects | Files accessible to anyone with anon key | Add storage policies for every bucket |
| Using public bucket for sensitive files | Data exposure | Use private buckets with signed URLs |
| Not setting file_size_limit | Users upload arbitrarily large files | Set limits on bucket creation |
| Missing allowed_mime_types | Users upload executable files | Restrict to expected file types |
| Hardcoding signed URL | URL expires, breaks after timeout | Generate fresh signed URLs on each request |
| Not cleaning up orphaned files | Storage bloat | Trigger file deletion on related record delete |
| Ignoring CDN cache on update | Stale content served | Use unique file names or cache-busting paths |
