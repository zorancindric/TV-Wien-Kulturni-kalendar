# TV Wien / TV Beč — Kulturni kalendar (rođendani & obljetnice)

Javni i automatski **iCalendar (ICS) feed** s rođendanima i obljetnicama smrti glumaca, glazbenika, slikara i drugih umjetnika. 
Kalendar se **svakodnevno obnavlja** (05:00 CET/CEST) i može se **pretplatiti u Google Kalendaru**.

## Što dobivate
- 📅 Dnevne all-day događaje: *Rođeni danas* i *Preminuli na današnji dan*
- 🎭 Područja: film/TV, kazalište, glazba, likovna umjetnost, književnost (moguće proširenje)
- 🔗 Linkovi na Wikidata (moguće proširenje na IMDb/MusicBrainz)
- 🌍 Više jezika: `hr`, `de`, `en` (odabir kroz env var `LANG`)

## Kako pokrenuti (GitHub Pages + Actions)
1. Napravite novi GitHub repozitorij, npr. `tvwien-cultural-calendar` i prenesite ove datoteke.
2. Uključite **GitHub Pages** na grani `gh-pages` (Settings → Pages).
3. U repozitoriju podesite **Actions** → dopuštenja (Settings → Actions → General → Workflow permissions → Read and write).
4. Commit/Push. Workflow će:
   - svako jutro u 05:00 (Europe/Vienna) pokrenuti skriptu
   - generirati `public/tvwien_cultural_calendar.ics`
   - objaviti na `gh-pages`, npr. `https://<username>.github.io/tvwien-cultural-calendar/tvwien_cultural_calendar.ics`

## Pretplata u Google Kalendar
- Otvorite Google Calendar → **Other calendars** → **+** → *From URL* → unesite URL `.ics` datoteke s GitHub Pages.
- Kalendar se sinkronizira automatski.

## Lokalno pokretanje
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_calendar.py --out public/tvwien_cultural_calendar.ics --lang hr --title "TV Wien – Kulturni kalendar" --tz Europe/Vienna
```

## Konfiguracija
- `config/occupations.json` — popis Wikidata zanimanja (QID-ovi) koji se uključuju.
- Varijable okoline (ENV):
  - `LANG` (`hr`|`de`|`en`) — jezik labela i tekstova (zadano: `hr`)
  - `TITLE` — naziv kalendara (zadano: "TV Wien – Kulturni kalendar")
  - `TZ` — vremenska zona (zadano: `Europe/Vienna`)

## Napomena
- Podaci dolaze primarno s **Wikidata** kroz SPARQL. 
- Kvaliteta i potpunost ovise o dostupnosti podataka (datumi i zanimanja).

— TV Wien / TV Beč
