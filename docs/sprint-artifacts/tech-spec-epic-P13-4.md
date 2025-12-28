# Epic Technical Specification: Branding

**Epic ID:** P13-4
**Phase:** 13 - Platform Maturity & External Integration
**Priority:** P3
**Generated:** 2025-12-28
**PRD Reference:** docs/PRD-phase13.md
**Epic Reference:** docs/epics-phase13.md

---

## Executive Summary

This epic implements consistent ArgusAI branding across all touchpoints - the main web app, documentation site, PWA manifest, native iOS/macOS apps, and social sharing previews. The logo source exists in `graphics/argusai-image.png` and needs to be exported to various sizes and formats.

**Functional Requirements Coverage:** FR27-FR32 (6 requirements)
**Backlog Reference:** IMP-039

---

## Architecture Overview

### Asset Requirements

| Asset | Size | Format | Location | Purpose |
|-------|------|--------|----------|---------|
| favicon.ico | 16x16, 32x32 | ICO | frontend/public | Browser tab icon |
| favicon-16x16.png | 16x16 | PNG | frontend/public | Standard favicon |
| favicon-32x32.png | 32x32 | PNG | frontend/public | Standard favicon |
| apple-touch-icon.png | 180x180 | PNG | frontend/public | iOS home screen |
| pwa-192.png | 192x192 | PNG | frontend/public | PWA manifest |
| pwa-512.png | 512x512 | PNG | frontend/public | PWA manifest |
| pwa-maskable-192.png | 192x192 | PNG | frontend/public | PWA maskable icon |
| pwa-maskable-512.png | 512x512 | PNG | frontend/public | PWA maskable icon |
| og-image.png | 1200x630 | PNG | frontend/public | Social sharing |
| logo.svg | Vector | SVG | frontend/public | Header logo |
| logo-dark.svg | Vector | SVG | frontend/public | Dark mode header |
| docs-logo.png | 100x100 | PNG | docs-site/static | Docs site header |
| docs-favicon.ico | 32x32 | ICO | docs-site/static | Docs site favicon |

### File Structure

```
graphics/
├── argusai-image.png           # Source logo (existing)
├── exports/                    # Generated exports (NEW)
│   ├── favicon.ico
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png
│   ├── pwa-192.png
│   ├── pwa-512.png
│   ├── pwa-maskable-192.png
│   ├── pwa-maskable-512.png
│   ├── og-image.png
│   ├── logo.svg
│   └── logo-dark.svg

frontend/public/
├── favicon.ico                 # REPLACE
├── favicon-16x16.png          # NEW
├── favicon-32x32.png          # NEW
├── apple-touch-icon.png       # REPLACE
├── icon-192.png               # REPLACE (PWA)
├── icon-512.png               # REPLACE (PWA)
├── icon-192-maskable.png      # NEW (PWA)
├── icon-512-maskable.png      # NEW (PWA)
├── og-image.png               # REPLACE
├── logo.svg                   # REPLACE
└── logo-dark.svg              # NEW

docs-site/static/img/
├── logo.png                   # REPLACE
├── favicon.ico                # REPLACE
└── og-image.png              # NEW
```

---

## Story Specifications

### Story P13-4.1: Export Logo Assets in Required Sizes

**Acceptance Criteria:**
- AC-4.1.1: Given the source logo, when export script runs, then all required sizes are generated
- AC-4.1.2: Given maskable icons are generated, when viewed, then safe zone padding is applied
- AC-4.1.3: Given exports complete, when verified, then all files pass quality checks

**Technical Specification:**

```bash
# scripts/export-logo-assets.sh
#!/bin/bash
# Export ArgusAI logo to all required sizes and formats
# Requires: ImageMagick (convert), librsvg (rsvg-convert)

set -e

SOURCE="graphics/argusai-image.png"
EXPORT_DIR="graphics/exports"

mkdir -p "$EXPORT_DIR"

echo "Exporting ArgusAI logo assets..."

# Standard favicons
convert "$SOURCE" -resize 16x16 "$EXPORT_DIR/favicon-16x16.png"
convert "$SOURCE" -resize 32x32 "$EXPORT_DIR/favicon-32x32.png"

# ICO file with multiple sizes
convert "$SOURCE" -resize 16x16 -define icon:auto-resize=16,32,48 "$EXPORT_DIR/favicon.ico"

# Apple Touch Icon (180x180 with padding for safe zone)
convert "$SOURCE" -resize 160x160 -gravity center -background white \
    -extent 180x180 "$EXPORT_DIR/apple-touch-icon.png"

# PWA icons (standard)
convert "$SOURCE" -resize 192x192 "$EXPORT_DIR/pwa-192.png"
convert "$SOURCE" -resize 512x512 "$EXPORT_DIR/pwa-512.png"

# PWA maskable icons (with safe zone - 80% of container)
# Maskable icons need padding for safe zone (10% on each side)
convert "$SOURCE" -resize 154x154 -gravity center -background white \
    -extent 192x192 "$EXPORT_DIR/pwa-maskable-192.png"
convert "$SOURCE" -resize 410x410 -gravity center -background white \
    -extent 512x512 "$EXPORT_DIR/pwa-maskable-512.png"

# Open Graph image (1200x630 with centered logo)
convert -size 1200x630 xc:#1a1a2e \
    \( "$SOURCE" -resize 300x300 \) -gravity center -composite \
    -font Arial -pointsize 64 -fill white -gravity south \
    -annotate +0+80 "ArgusAI" \
    "$EXPORT_DIR/og-image.png"

# Docs site assets
convert "$SOURCE" -resize 100x100 "$EXPORT_DIR/docs-logo.png"

# Generate SVG (trace from PNG - or use source SVG if available)
# For now, just copy and resize for use
convert "$SOURCE" -resize 40x40 "$EXPORT_DIR/logo-header.png"

echo "Logo export complete. Files in $EXPORT_DIR/"
ls -la "$EXPORT_DIR/"
```

**Alternative Python Script:**
```python
# scripts/export_logo_assets.py
from PIL import Image
import os

SOURCE = "graphics/argusai-image.png"
EXPORT_DIR = "graphics/exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

def export_png(source, size, output, padding=0):
    """Export PNG at specified size with optional padding."""
    img = Image.open(source)

    if padding:
        # Resize smaller to add padding
        inner_size = int(size * (1 - padding * 2))
        img = img.resize((inner_size, inner_size), Image.LANCZOS)

        # Create padded image
        padded = Image.new('RGBA', (size, size), (255, 255, 255, 255))
        offset = (size - inner_size) // 2
        padded.paste(img, (offset, offset), img)
        padded.save(output)
    else:
        img = img.resize((size, size), Image.LANCZOS)
        img.save(output)

    print(f"Exported: {output}")

# Standard exports
export_png(SOURCE, 16, f"{EXPORT_DIR}/favicon-16x16.png")
export_png(SOURCE, 32, f"{EXPORT_DIR}/favicon-32x32.png")
export_png(SOURCE, 180, f"{EXPORT_DIR}/apple-touch-icon.png", padding=0.05)
export_png(SOURCE, 192, f"{EXPORT_DIR}/pwa-192.png")
export_png(SOURCE, 512, f"{EXPORT_DIR}/pwa-512.png")

# Maskable icons with 10% safe zone padding
export_png(SOURCE, 192, f"{EXPORT_DIR}/pwa-maskable-192.png", padding=0.10)
export_png(SOURCE, 512, f"{EXPORT_DIR}/pwa-maskable-512.png", padding=0.10)

# Docs
export_png(SOURCE, 100, f"{EXPORT_DIR}/docs-logo.png")

# Create OG image (1200x630)
og = Image.new('RGB', (1200, 630), (26, 26, 46))  # Dark background
logo = Image.open(SOURCE).resize((300, 300), Image.LANCZOS)
og.paste(logo, (450, 120), logo)
og.save(f"{EXPORT_DIR}/og-image.png")
print(f"Exported: {EXPORT_DIR}/og-image.png")

print("\nExport complete!")
```

**Files to Create:**
- `scripts/export-logo-assets.sh` or `scripts/export_logo_assets.py` (NEW)
- `graphics/exports/` directory with all assets (NEW)

---

### Story P13-4.2: Update Frontend Branding

**Acceptance Criteria:**
- AC-4.2.1: Given the frontend loads, when viewing browser tab, then ArgusAI favicon is displayed
- AC-4.2.2: Given the PWA manifest, when installing as app, then correct icons appear
- AC-4.2.3: Given sharing on social media, when Open Graph is rendered, then ArgusAI branded image shows

**Technical Specification:**

```tsx
// frontend/app/layout.tsx - MODIFY
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'ArgusAI - AI-Powered Home Security',
  description: 'Intelligent event detection for your home cameras',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
  manifest: '/manifest.json',
  openGraph: {
    title: 'ArgusAI - AI-Powered Home Security',
    description: 'Intelligent event detection for your home cameras',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'ArgusAI Logo',
      },
    ],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ArgusAI - AI-Powered Home Security',
    description: 'Intelligent event detection for your home cameras',
    images: ['/og-image.png'],
  },
}
```

```json
// frontend/public/manifest.json - MODIFY
{
  "name": "ArgusAI",
  "short_name": "ArgusAI",
  "description": "AI-Powered Home Security",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#6366f1",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    },
    {
      "src": "/icon-192-maskable.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/icon-512-maskable.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
```

```tsx
// frontend/components/layout/Header.tsx - MODIFY
import Image from 'next/image';

export function Header() {
  return (
    <header className="border-b">
      <div className="container flex h-16 items-center">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/logo.svg"
            alt="ArgusAI"
            width={32}
            height={32}
            className="dark:hidden"
          />
          <Image
            src="/logo-dark.svg"
            alt="ArgusAI"
            width={32}
            height={32}
            className="hidden dark:block"
          />
          <span className="font-bold text-xl">ArgusAI</span>
        </Link>
        {/* ... rest of header */}
      </div>
    </header>
  );
}
```

**Files to Modify:**
- `frontend/app/layout.tsx` (MODIFY)
- `frontend/public/manifest.json` (MODIFY)
- `frontend/components/layout/Header.tsx` (MODIFY)
- Copy assets from `graphics/exports/` to `frontend/public/`

---

### Story P13-4.3: Update Docs Site Branding

**Acceptance Criteria:**
- AC-4.3.1: Given the docs site, when viewing, then ArgusAI logo appears in navbar
- AC-4.3.2: Given the docs site, when viewing browser tab, then ArgusAI favicon is displayed
- AC-4.3.3: Given sharing docs site link, when Open Graph renders, then ArgusAI branded image shows

**Technical Specification:**

```javascript
// docs-site/docusaurus.config.js - MODIFY
const config = {
  title: 'ArgusAI Documentation',
  tagline: 'AI-Powered Home Security',
  favicon: 'img/favicon.ico',
  url: 'https://project-argusai.github.io',
  baseUrl: '/argusai/',
  organizationName: 'project-argusai',
  projectName: 'argusai',

  themeConfig: {
    image: 'img/og-image.png',
    navbar: {
      title: 'ArgusAI',
      logo: {
        alt: 'ArgusAI Logo',
        src: 'img/logo.png',
        srcDark: 'img/logo-dark.png',
      },
      items: [
        { type: 'doc', docId: 'intro', position: 'left', label: 'Docs' },
        { to: '/api', label: 'API', position: 'left' },
        {
          href: 'https://github.com/project-argusai/ArgusAI',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      logo: {
        alt: 'ArgusAI',
        src: 'img/logo.png',
        width: 40,
      },
      copyright: `Copyright ${new Date().getFullYear()} ArgusAI. Built with Docusaurus.`,
    },
  },
};
```

**Files to Modify:**
- `docs-site/docusaurus.config.js` (MODIFY)
- Copy assets to `docs-site/static/img/`:
  - `logo.png`
  - `logo-dark.png`
  - `favicon.ico`
  - `og-image.png`

---

## Accessibility Requirements

All logo assets must pass these accessibility checks:

| Check | Requirement | Tool |
|-------|-------------|------|
| Contrast Ratio | 4.5:1 minimum against backgrounds | WebAIM Contrast Checker |
| Alt Text | All `<img>` tags have descriptive alt | Manual review |
| Dark Mode | Logos visible in both light/dark modes | Visual inspection |

---

## Quality Checklist

Before merging, verify:

- [ ] All PNG files are optimized (use pngquant or similar)
- [ ] favicon.ico contains 16x16 and 32x32 variants
- [ ] Maskable icons have proper safe zone padding
- [ ] OG image dimensions are exactly 1200x630
- [ ] SVG files are properly viewBoxed
- [ ] Dark mode variants exist where needed
- [ ] No placeholder/default Next.js icons remain

---

## Testing Strategy

### Visual Tests
- Load frontend in multiple browsers (Chrome, Firefox, Safari, Edge)
- Install as PWA and verify icon appearance
- Share page on Twitter/LinkedIn and verify OG image
- Test dark mode logo switching

### Automated Tests
- Lighthouse audit for PWA icon requirements
- HTML validation for proper meta tags
- Image size validation script

---

## Dependencies

### Tools Required
- ImageMagick (for bash script)
- Pillow (for Python script)
- Optional: svgo for SVG optimization
- Optional: pngquant for PNG optimization
