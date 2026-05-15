# LaTeX Resume Templates

Sources: Modern CV/Resume LaTeX guides, Overleaf templates, GitHub tech resume repositories

Covers: Clean LaTeX templates that produce ATS-friendly PDF output — agents compile easily.

## Why LaTeX for Tech Resumes

- **Clean text extraction** — ATS parses plain text perfectly
- **Consistent formatting** — Every compile = identical output
- **Version control** — Git-friendly, diffable, agent-editable
- **Industry standard** — Google, Stripe, academic roles expect it
- **Compilation easy** — Agents use pdflatex/xelatex naturally

## Template 1: Entry-Level Engineer

### When to Use

- 0-2 years experience
- Strong projects section
- Bootcamp graduates
- Career changers

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[left=0.75in,right=0.75in,top=0.5in,bottom=0.5in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}

% Formatting
\pagestyle{empty}
\titleformat{\section}{\bfseries\uppercase}{}{0pt}{}
\titlespacing{\section}{0pt}{6pt}{4pt}

\begin{document}

% HEADER
\textbf{Name} \hfill \hrefmailto{email@example.com}{email@example.com}
\\
Role Title \hfill \href{https://github.com/username}{GitHub} $\mid$ \href{https://linkedin.com/in/username}{LinkedIn}

\section*{Professional Summary}
Entry-level software engineer with expertise in Python and JavaScript.
Built 3 full-stack projects using React and Django. Seeking to apply
strong problem-solving skills to impactful products.

\section*{Technical Skills}
\begin{tabular}{ll}
Languages: & Python, JavaScript, Go, SQL \\
Frameworks: & React, Node.js, Django, FastAPI \\
Tools: & Git, Docker, AWS, Linux \\
\end{tabular}

\section*{Experience}
\textbf{Software Engineering Intern} \hfill Company Name \textit{May--Aug 2024}
\begin{itemize}
  \item Developed REST API endpoints using Python and Flask, serving 5K daily requests
  \item Built automated testing suite reducing bug escape rate by 30\%
  \item Collaborated with team of 5 engineers on sprint planning and code reviews
\end{itemize}

\textbf{Teaching Assistant} \hfill Bootcamp Name \textit{Jan--April 2024}
\begin{itemize}
  \item Mentored 15 students on Python, data structures, and web development
  \item Graded assignments and provided feedback on code quality and best practices
\end{itemize}

\section*{Projects}
\textbf{Project Name} \hfill \href{https://github.com/user/project}{GitHub}
\begin{itemize}
  \item Built full-stack web app using React, Node.js, and PostgreSQL
  \item Implemented authentication and real-time features using WebSocket
  \item Deployed on AWS EC2, serving 500+ monthly active users
\end{itemize}

\textbf{Another Project} \hfill \href{https://github.com/user/project2}{GitHub}
\begin{itemize}
  \item Created machine learning model achieving 92\% accuracy on image classification
  \item Optimized inference time by 40\% using model quantization
\end{itemize}

\section*{Education}
\textbf{Bachelor of Science in Computer Science} \hfill University Name \textit{2020--2024}
\begin{itemize}
  \item GPA: 3.7/4.0, Dean's List
  \item Relevant Coursework: Data Structures, Algorithms, Databases, Operating Systems
\end{itemize}

\end{document}
```

## Template 2: Senior Engineer

### When to Use

- 5+ years experience
- Leadership/architecture focus
- Team management

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[left=0.75in,right=0.75in,top=0.5in,bottom=0.5in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}

\pagestyle{empty}
\titleformat{\section}{\bfseries\uppercase}{}{0pt}{}
\titlespacing{\section}{0pt}{6pt}{4pt}

\begin{document}

% HEADER
\textbf{Name} \hfill \hrefmailto{email@example.com}{email@example.com}
\\
Senior Software Engineer \hfill \href{https://github.com/username}{GitHub} $\mid$ \href{https://linkedin.com/in/username}{LinkedIn}

\section*{Technical Skills}
\begin{tabular}{ll}
Languages: & Python, Go, TypeScript, SQL \\
Backend: & Django, FastAPI, gRPC, PostgreSQL, Redis \\
Cloud: & AWS (EC2, ECS, Lambda, RDS), Terraform \\
DevOps: & Docker, Kubernetes, CI/CD, Prometheus \\
\end{tabular}

\section*{Professional Experience}
\textbf{Senior Software Engineer} \hfill Company Name \textit{2021--Present}
\begin{itemize}
  \item Architected microservices handling 2M+ daily requests, reducing latency by 45\%
  \item Led team of 4 engineers, conducted 100+ code reviews, established team coding standards
  \item Implemented CI/CD pipelines cutting deployment time from 2 hours to 15 minutes
  \item Mentored 2 junior engineers, both promoted to mid-level within 18 months
\end{itemize}

\textbf{Software Engineer} \hbar Company Name \textit{2018--2021}
\begin{itemize}
  \item Built real-time analytics dashboard using React and Python, serving 500+ internal users
  \item Optimized database queries reducing report generation time from 30s to 2s
  \item Developed Python scripts automating manual reporting, saving 20 hours/week
\end{itemize}

\section*{Education}
\textbf{B.S. Computer Science} \hbar University Name \textit{2014--2018}

\section*{Certifications}
AWS Certified Solutions Architect (2023), Certified Kubernetes Administrator (2022)

\end{document}
```

## Template 3: Full-Stack Developer

### When to Use

- Frontend + backend experience
- Modern JavaScript stack
- Project complexity

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[left=0.75in,right=0.75in,top=0.5in,bottom=0.5in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}

\pagestyle{empty}
\titleformat{\section}{\bfseries\uppercase}{}{0pt}{}
\titlespacing{\section}{0pt}{6pt}{4pt}

\begin{document}

\textbf{Name} \hfill \hrefmailto{email@example.com}{email@example.com}
\\
Full-Stack Developer \hfill \href{https://github.com/username}{GitHub} $\mid$ \href{https://linkedin.com/in/username}{LinkedIn}

\section*{Technical Skills}
Frontend: React, TypeScript, Next.js, Redux, Tailwind CSS, Jest, Cypress \\
Backend: Node.js, Express, Python, Django, PostgreSQL, Redis, GraphQL \\
Tools: Git, Docker, AWS, Firebase, Figma

\section*{Professional Experience}
\textbf{Full-Stack Developer} \hbar Company Name \textit{2022--Present}
\begin{itemize}
  \item Built customer-facing portal using React and Node.js, increasing user engagement by 60\%
  \item Designed and implemented GraphQL API replacing REST, reducing payload size by 70\%
  \item Developed reusable component library used across 5 projects
  \item Wrote integration tests achieving 85\% code coverage
\end{itemize}

\textbf{Frontend Developer} \hbar Company Name \textit{2020--2022}
\begin{itemize}
  \item Migrated legacy jQuery codebase to React, improving page load time by 50\%
  \item Implemented responsive designs for mobile-first web application
  \item Created automation scripts reducing deployment manual work by 80\%
\end{itemize}

\section*{Projects}
\textbf{Open Source Contribution} \hbar \href{https://github.com/user/repo}{React Router}
\begin{itemize}
  \item Contributed bug fixes and documentation improvements to popular routing library
  \item PRs merged: 5, GitHub stars increased: 500+
\end{itemize}

\section*{Education}
\textbf{B.S. Software Engineering} \hbar State University \textit{2016--2020}

\end{document}
```

## Template 4: DevOps Engineer

### When to Use

- Infrastructure focus
- Cloud + containers
- CI/CD pipelines

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[left=0.75in,right=0.75in,top=0.5in,bottom=0.5in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}

\pagestyle{empty}
\titleformat{\section}{\bfseries\uppercase}{}{0pt}{}
\titlespacing{\section}{0pt}{6pt}{4pt}

\begin{document}

\textbf{Name} \hbar \hrefmailto{email@example.com}{email@example.com}
\\
DevOps Engineer \hbar \href{https://github.com/username}{GitHub} $\mid$ \href{https://linkedin.com/in/username}{LinkedIn}

\section*{Technical Skills}
Cloud: AWS, GCP, Azure \\
Container: Docker, Kubernetes, Helm, EKS/GKE \\
CI/CD: Jenkins, GitLab CI, GitHub Actions, ArgoCD \\
IaC: Terraform, CloudFormation, Pulumi \\
Monitoring: Prometheus, Grafana, ELK, Datadog \\
Scripting: Python, Bash, Go

\section*{Professional Experience}
\textbf{Senior DevOps Engineer} \hbar Company Name \textit{2021--Present}
\begin{itemize}
  \item Designed and implemented Kubernetes clusters on AWS EKS, reducing infrastructure costs by 40\%
  \item Built CI/CD pipelines using GitLab CI, deploying 50+ services with zero-downtime
  \item Implemented infrastructure monitoring with Prometheus and Grafana, reducing MTTR by 60\%
  \item Established security scanning in CI/CD pipeline, catching 100+ vulnerabilities pre-deploy
\end{itemize}

\textbf{DevOps Engineer} \hbar Company Name \textit{2019--2021}
\begin{itemize}
  \item Migrated monolithic application to containerized microservices using Docker and Kubernetes
  \item Automated infrastructure provisioning with Terraform, reducing provisioning time from 2 days to 30 minutes
  \item Implemented centralized logging with ELK stack, enabling faster incident diagnosis
\end{itemize}

\section*{Certifications}
AWS Certified Solutions Architect Professional, CKA, CKAD, HashiCorp Terraform Associate

\section*{Education}
\textbf{B.S. Computer Science} \hbar University Name \textit{2015--2019}

\end{document}
```

## LaTeX Tips for ATS

### Compilation

```bash
# Standard compilation
pdflatex resume.tex

# With XeTeX for better font support
xelatex resume.tex

# Multiple passes (for TOC/references)
pdflatex resume.tex
pdflatex resume.tex
```

### Packages to Include

```latex
\usepackage{hyperref}     % Links in PDF (don't worry, ATS reads text)
\usepackage{enumitem}    % Better bullet formatting
\usepackage{titlesec}    % Section formatting control
```

### What to Avoid

- Custom fonts that don't embed (use standard: Computer Modern, Latin Modern)
- Complex table structures ( ATS may break )
- Colored text (often not parsed)
- Very complex layouts

### What Works Well

- Single column
- Standard section headers
- Plain text content
- Simple tables (skills lists)
- Consistent formatting

## Agent-Friendly Notes

When generating with AI:

1. **Ask for LaTeX output** — "Write this resume in LaTeX format"
2. **Specify compiler** — "Use pdflatex"
3. **Check dependencies** — Most systems have texlive installed
4. **Test compile** — Ensure it builds before sending
5. **PDF output** — Convert to PDF for ATS submission