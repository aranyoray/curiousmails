# Deployment Guide - ISEF Winners Table

## Quick Deploy to Vercel

### Option 1: Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Option 2: Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your Git repository
4. Vercel will auto-detect the configuration from `vercel.json`
5. Click "Deploy"

## Files Structure

```
curiousmails/
├── winners-table.html       # Main table interface
├── vercel.json              # Vercel configuration
├── data/
│   ├── winner_emails.json   # Winner contact data
│   └── projects.json        # Full projects database
├── email_scraper.py         # Email scraper script
├── enhance_winner_data.py   # Data enhancement script
└── generate_table_data.py   # Table formatter
```

## Features

### Interactive Table
- **Search**: Real-time filtering across all fields
- **Sort**: Click column headers to sort
- **Copy**: Click "Copy Table" to copy all data to clipboard
- **Export**: Download as CSV file

### Table Columns
- **Uni**: University (extracted from awards)
- **Year**: Competition year
- **First**: First name
- **Last**: Last name
- **Major**: Science category/major
- **Email**: Contact email (if found)
- **Notes**: Awards received

## Customization

### Update Winner Data

Run the email scraper for more winners:

```bash
# Scrape emails for 100 winners
python3 email_scraper.py 100

# Enhance with category data
python3 enhance_winner_data.py

# Preview table
python3 generate_table_data.py
```

### Filter Different Years

Edit `email_scraper.py` line 298 to change the year filter:

```python
# Change 2019 to your desired start year
if int(year) >= 2019 and awards:
```

### Customize Styling

Edit `winners-table.html` CSS section (lines 12-226) to change:
- Colors and gradients
- Table layout
- Fonts and typography
- Mobile responsiveness

## Local Development

```bash
# Simple HTTP server
python -m http.server 8000

# Open browser
open http://localhost:8000/winners-table.html
```

## Environment Variables

No environment variables needed! The app is completely static.

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers supported

## Performance

- Loads 1000s of winners instantly
- Client-side search and filtering
- No backend required
- Fully static deployment

## Deployment URLs

After deploying to Vercel, you'll get a URL like:

- Production: `https://curiousmails.vercel.app`
- Preview: `https://curiousmails-git-branch.vercel.app`

## Support

For issues or questions:
- Check the [main README](README.md)
- Review the source code comments
- Test locally first before deploying

---

**Live Demo**: Deploy to see the interactive table in action!
