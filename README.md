# Anthony's GitHub Pages site

A deliberately small static site: plain HTML, one CSS file, MathJax for LaTeX, and SVG for figures.

## Structure

- `index.html` — Anthony/about page, including short selected-work descriptions
- `cv.html` — temporary HTML CV page linked from the Anthony page (not a top-level tab)
- `blog/index.html` — blog index
- `blog/example.html` — sample MathJax + SVG post
- `blog/_template.html` — copy this when starting a new post
- `assets/style.css` — all styling
- `assets/example-plot.svg` — example graph

## Add a blog post

Copy `blog/_template.html`, rename it, edit the title/date/body, then add the new post to `blog/index.html`.

Math works with normal MathJax notation:

```html
\(L(B)=B\mathbb{Z}^n\)

\[
  \lambda_1(L)=\min_{x\in L\setminus\{0\}} \lVert x\rVert.
\]
```

For graphs, export SVG and put it in `assets/`, then use:

```html
<img src="../assets/my-figure.svg" alt="Description of the figure">
```
