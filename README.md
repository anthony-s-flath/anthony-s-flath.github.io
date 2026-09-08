# Temporary anthonyflath.com GitHub Pages site

A deliberately small static site: plain HTML, one CSS file, MathJax for LaTeX, and SVG for figures.

## Structure

- `index.html` — Anthony/about page, including short selected-work descriptions
- `cv.html` — temporary HTML CV page linked from the Anthony page (not a top-level tab)
- `blog/index.html` — blog index
- `blog/example.html` — sample MathJax + SVG post
- `blog/_template.html` — copy this when starting a new post
- `assets/style.css` — all styling
- `assets/example-plot.svg` — example graph
- `.nojekyll` — tells GitHub Pages to serve the files as-is

Top-level navigation is intentionally only **Anthony · Blog**. There is **no Projects tab** and no CV tab. If a project is worth showing, add one short item under “Selected work” on `index.html`.

## Publish with GitHub Pages

1. Create a repository, e.g. `anthony-s-flath.github.io` for a user site.
2. Copy these files to the repository root.
3. Push the `main` branch.
4. In GitHub: **Settings → Pages → Build and deployment → Deploy from a branch**.
5. Select `main` and `/ (root)`.

For a custom domain, add the domain in GitHub Pages settings after the temporary site is working. GitHub can create/manage the `CNAME` file from that setting.

## Add a blog post

Copy `blog/_template.html`, rename it, edit the title/date/body, then add the new post to `blog/index.html`.

Math works with normal MathJax notation:

```html
\(L(B)=B\mathbb{Z}^n\)

\[
  \lambda_1(L)=\min_{x\in L\setminus\{0\}} \lVert x\rVert.
\]
```

For research graphs, export SVG and put it in `assets/`, then use:

```html
<img src="../assets/my-figure.svg" alt="Description of the figure">
```
