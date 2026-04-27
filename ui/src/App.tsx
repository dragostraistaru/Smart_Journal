import { useEffect, useMemo, useState } from 'react'

import './App.css'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

type ApiEntry = {
  id: number
  user_id: number
  title: string
  content: string
  entry_date: string
  mood_label: string | null
  mood_confidence: number | null
  created_at: string
  updated_at: string
}

type CalendarEntry = {
  id: number
  dateIso: string
  day: number
  title: string
  content: string
  time: string
  category: string
  tone: 'yellow' | 'orange' | 'blue' | 'pink' | 'violet' | 'red'
}

type CalendarCell = {
  iso: string
  day: number
  inCurrentMonth: boolean
}

const dayNames = ['LUN', 'MAR', 'MIE', 'JOI', 'VIN', 'SAM', 'DUM']

function toIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function toneFromMood(mood: string | null): CalendarEntry['tone'] {
  if (!mood) {
    return 'yellow'
  }

  const normalized = mood.toLowerCase()
  if (normalized.includes('anx')) {
    return 'red'
  }
  if (normalized.includes('calm')) {
    return 'blue'
  }
  if (normalized.includes('neutral')) {
    return 'yellow'
  }
  return 'violet'
}

function buildCalendarCells(currentMonth: Date): CalendarCell[] {
  const year = currentMonth.getFullYear()
  const month = currentMonth.getMonth()
  const firstDay = new Date(year, month, 1)
  const mondayOffset = (firstDay.getDay() + 6) % 7
  const startDate = new Date(year, month, 1 - mondayOffset)

  return Array.from({ length: 42 }, (_, index) => {
    const cellDate = new Date(startDate)
    cellDate.setDate(startDate.getDate() + index)
    return {
      iso: toIsoDate(cellDate),
      day: cellDate.getDate(),
      inCurrentMonth: cellDate.getMonth() === month,
    }
  })
}

function App() {
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), 1)
  })
  const [userId, setUserId] = useState<number | null>(null)
  const [entries, setEntries] = useState<ApiEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState('')
  const [isEntryFormOpen, setIsEntryFormOpen] = useState(false)
  const [entryFormMode, setEntryFormMode] = useState<'create' | 'edit'>('create')
  const [editingEntryId, setEditingEntryId] = useState<number | null>(null)
  const [entryTitle, setEntryTitle] = useState('')
  const [entryContent, setEntryContent] = useState('')
  const [entryDate, setEntryDate] = useState(() => toIsoDate(new Date()))
  const [isSavingEntry, setIsSavingEntry] = useState(false)
  const [isDeletingEntry, setIsDeletingEntry] = useState(false)

  const [activeCategory, setActiveCategory] = useState('Toate intrarile')
  const [searchTerm, setSearchTerm] = useState('')
  const [activeSection, setActiveSection] = useState('Jurnal')

  const monthLabel = useMemo(() => {
    return new Intl.DateTimeFormat('ro-RO', { month: 'long', year: 'numeric' }).format(currentMonth)
  }, [currentMonth])

  const categories = useMemo(() => {
    const uniqueTitles = [...new Set(entries.map((entry) => entry.title))]
    return ['Toate intrarile', ...uniqueTitles]
  }, [entries])

  const mappedEntries = useMemo<CalendarEntry[]>(() => {
    return entries.map((entry) => {
      const dateParts = entry.entry_date.split('-')
      const day = Number(dateParts[2])
      const createdAt = new Date(entry.created_at)
      const time = Number.isNaN(createdAt.getTime())
        ? '--:--'
        : createdAt.toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' })

      return {
        id: entry.id,
        dateIso: entry.entry_date,
        day,
        title: entry.title,
        content: entry.content,
        time,
        category: entry.mood_label ?? 'Jurnal',
        tone: toneFromMood(entry.mood_label),
      }
    })
  }, [entries])

  const calendarCells = useMemo(() => buildCalendarCells(currentMonth), [currentMonth])

  const visibleEntries = useMemo(() => {
    return mappedEntries.filter((entry) => {
      const matchesCategory =
        activeCategory === 'Toate intrarile' || entry.title === activeCategory
      const matchesSearch =
        searchTerm.trim().length === 0 ||
        `${entry.title} ${entry.category} ${entry.time} ${entry.content}`
          .toLowerCase()
          .includes(searchTerm.trim().toLowerCase())

      return matchesCategory && matchesSearch
    })
  }, [activeCategory, mappedEntries, searchTerm])

  function closeEntryForm(): void {
    setIsEntryFormOpen(false)
    setEditingEntryId(null)
  }

  function openCreateEntryForm(): void {
    if (!userId) {
      setStatusMessage('Nu exista user activ. Verifica API-ul.')
      return
    }

    setEntryFormMode('create')
    setEditingEntryId(null)
    setEntryTitle('')
    setEntryContent('')
    setEntryDate(toIsoDate(new Date()))
    setIsEntryFormOpen(true)
    setStatusMessage('Completeaza formularul de intrare noua.')
  }

  function openEditEntryForm(entryId: number): void {
    if (!userId) {
      setStatusMessage('Nu exista user activ. Verifica API-ul.')
      return
    }

    const entry = entries.find((currentEntry) => currentEntry.id === entryId)
    if (!entry) {
      setStatusMessage('Nu am gasit intrarea selectata.')
      return
    }

    setEntryFormMode('edit')
    setEditingEntryId(entry.id)
    setEntryTitle(entry.title)
    setEntryContent(entry.content)
    setEntryDate(entry.entry_date)
    setIsEntryFormOpen(true)
    setStatusMessage('Editezi intrarea selectata.')
  }

  async function loadEntries(forUserId: number): Promise<void> {
    const response = await fetch(`${API_BASE}/api/entries?user_id=${forUserId}`)
    if (!response.ok) {
      throw new Error('Nu am putut incarca intrarile din backend.')
    }
    const payload = (await response.json()) as ApiEntry[]
    setEntries(payload)
  }

  useEffect(() => {
    async function bootstrap(): Promise<void> {
      try {
        const userResponse = await fetch(`${API_BASE}/api/users/bootstrap`, { method: 'POST' })
        if (!userResponse.ok) {
          throw new Error('Nu am putut initializa utilizatorul demo.')
        }

        const userPayload = (await userResponse.json()) as { id: number; email: string }
        setUserId(userPayload.id)
        await loadEntries(userPayload.id)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Eroare necunoscuta de conectare la API.'
        setStatusMessage(message)
      } finally {
        setIsLoading(false)
      }
    }

    void bootstrap()
  }, [])

  async function submitCreateEntry(): Promise<void> {
    if (!userId) {
      setStatusMessage('Nu exista user activ. Verifica API-ul.')
      return
    }

    const title = entryTitle.trim()
    const content = entryContent.trim()
    const selectedDate = entryDate.trim()

    if (!title || !content) {
      setStatusMessage('Titlul si continutul sunt obligatorii.')
      return
    }

    if (!/^\d{4}-\d{2}-\d{2}$/.test(selectedDate)) {
      setStatusMessage('Data invalida. Foloseste formatul YYYY-MM-DD.')
      return
    }

    try {
      setIsSavingEntry(true)
      const isEditMode = entryFormMode === 'edit'
      const response = await fetch(
        isEditMode && editingEntryId !== null
          ? `${API_BASE}/api/entries/${editingEntryId}`
          : `${API_BASE}/api/entries`,
        {
        method: isEditMode ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          title,
          content,
          entry_date: selectedDate,
        }),
        },
      )

      if (!response.ok) {
        const detail = (await response.json()) as { detail?: string }
        throw new Error(detail.detail ?? 'Nu am putut salva intrarea.')
      }

      await loadEntries(userId)
      closeEntryForm()
      setStatusMessage(isEditMode ? 'Intrarea a fost actualizata.' : 'Intrarea a fost salvata in backend.')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Eroare la salvare.'
      setStatusMessage(message)
    } finally {
      setIsSavingEntry(false)
    }
  }

  async function deleteCurrentEntry(): Promise<void> {
    if (!userId || editingEntryId === null) {
      setStatusMessage('Nu exista intrare selectata pentru stergere.')
      return
    }

    const confirmed = window.confirm('Stergi aceasta intrare?')
    if (!confirmed) {
      return
    }

    try {
      setIsDeletingEntry(true)
      const response = await fetch(`${API_BASE}/api/entries/${editingEntryId}?user_id=${userId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const detail = (await response.json()) as { detail?: string }
        throw new Error(detail.detail ?? 'Nu am putut sterge intrarea.')
      }

      await loadEntries(userId)
      closeEntryForm()
      setStatusMessage('Intrarea a fost stearsa.')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Eroare la stergere.'
      setStatusMessage(message)
    } finally {
      setIsDeletingEntry(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <button className="menu-button" aria-label="Meniu">
            ≡
          </button>
          <span className="brand">Smart Journal</span>
        </div>

        <p className="section-title">CATEGORII</p>
        <nav className="categories">
          {categories.map((category) => (
            <button
              key={category}
              className={`category ${activeCategory === category ? 'active' : ''}`}
              onClick={() => setActiveCategory(category)}
            >
              {category}
            </button>
          ))}
          <button
            className="category add"
            onClick={() => alert('In iteratia 1 asta e doar mock UI. Aici vei crea o categorie noua.')}
          >
            + Categorie noua
          </button>
        </nav>

        <article className="streak-card">
          <strong>{visibleEntries.length}</strong>
          <span>intrari vizibile</span>
        </article>

        <footer className="bottom-nav">
          {['Jurnal', 'Dashboard', 'Rezumate'].map((section) => (
            <button
              key={section}
              className={`nav-item ${activeSection === section ? 'active' : ''}`}
              onClick={() => setActiveSection(section)}
            >
              {section}
            </button>
          ))}
        </footer>
      </aside>

      <main className="board">
        <header className="topbar">
          <h1>Jurnalul meu</h1>
          <div className="topbar-actions">
            <input
              type="search"
              placeholder="Cauta intrare..."
              aria-label="Cauta intrare"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
            />
            <button className="primary" onClick={openCreateEntryForm}>
              + Intrare noua
            </button>
          </div>
        </header>

        {isLoading && <p className="status-line">Se incarca datele din backend...</p>}
        {!isLoading && statusMessage && <p className="status-line">{statusMessage}</p>}

        <div className="month-line">
          <button
            aria-label="Luna anterioara"
            onClick={() =>
              setCurrentMonth((current) =>
                new Date(current.getFullYear(), current.getMonth() - 1, 1),
              )
            }
          >
            ‹ prev.
          </button>
          <strong>{monthLabel}</strong>
          <button
            aria-label="Luna urmatoare"
            onClick={() =>
              setCurrentMonth((current) =>
                new Date(current.getFullYear(), current.getMonth() + 1, 1),
              )
            }
          >
            next ›
          </button>
        </div>

        <section className="calendar" aria-label="Calendar jurnal">
          {dayNames.map((name) => (
            <div key={name} className="head-cell">
              {name}
            </div>
          ))}

          {calendarCells.map((cell) => {
            const dayEntries = visibleEntries.filter((entry) => entry.dateIso === cell.iso)

            return (
              <article key={cell.iso} className={`day-cell ${cell.inCurrentMonth ? '' : 'muted'}`}>
                <span className="day-number">{cell.day}</span>
                <div className="entry-stack">
                  {dayEntries.map((entry, cardIndex) => (
                    <div
                      key={entry.id}
                      className={`entry-card ${entry.tone}`}
                      style={{ animationDelay: `${cardIndex * 80}ms` }}
                      role="button"
                      tabIndex={0}
                      onClick={() => openEditEntryForm(entry.id)}
                    >
                      <b>{entry.title}</b>
                      <small>{entry.time}</small>
                      <em>{entry.category}</em>
                    </div>
                  ))}
                </div>
              </article>
            )
          })}
        </section>

        {isEntryFormOpen && (
          <div className="entry-modal" role="dialog" aria-modal="true" aria-labelledby="create-entry-title">
            <div className="entry-modal-card">
              <div className="entry-modal-header">
                <div>
                  <p className="entry-modal-kicker">Jurnal</p>
                  <h2 id="create-entry-title">
                    {entryFormMode === 'edit' ? 'Editeaza intrare' : 'Intrare noua'}
                  </h2>
                </div>
                <button
                  className="entry-modal-close"
                  onClick={closeEntryForm}
                  aria-label="Inchide formularul"
                  type="button"
                >
                  ×
                </button>
              </div>

              <label className="entry-field">
                <span>Titlu</span>
                <input
                  type="text"
                  value={entryTitle}
                  onChange={(event) => setEntryTitle(event.target.value)}
                  placeholder="Ex. Dimineata linistita"
                  autoFocus
                />
              </label>

              <label className="entry-field">
                <span>Continut</span>
                <textarea
                  value={entryContent}
                  onChange={(event) => setEntryContent(event.target.value)}
                  placeholder="Scrie ce s-a intamplat azi..."
                  rows={6}
                />
              </label>

              <label className="entry-field">
                <span>Data</span>
                <input
                  type="date"
                  value={entryDate}
                  onChange={(event) => setEntryDate(event.target.value)}
                />
              </label>

              <div className="entry-modal-actions">
                {entryFormMode === 'edit' && (
                  <button className="danger" onClick={() => void deleteCurrentEntry()} type="button" disabled={isDeletingEntry}>
                    {isDeletingEntry ? 'Se sterge...' : 'Sterge intrarea'}
                  </button>
                )}
                <button className="secondary" onClick={closeEntryForm} type="button">
                  Renunta
                </button>
                <button
                  className="primary"
                  onClick={() => void submitCreateEntry()}
                  type="button"
                  disabled={isSavingEntry}
                >
                  {isSavingEntry
                    ? 'Se salveaza...'
                    : entryFormMode === 'edit'
                      ? 'Actualizeaza intrarea'
                      : 'Salveaza intrarea'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
