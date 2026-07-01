# Unsafe content

<div onclick="alert('xss')">click me</div>

<script>window.__unsafe = true;</script>

<svg viewBox="0 0 10 10" onload="window.__svgUnsafe = true">
  <circle cx="5" cy="5" r="4"></circle>
</svg>
