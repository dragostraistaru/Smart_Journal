import { useCallback, useEffect, useMemo, useState, useRef } from 'react'

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

type DashboardStats = {
  total_entries: number
  current_month_entries: number
  writing_days: number
  average_mood_confidence: number
  top_mood: string
  mood_distribution: {
    mood: string
    count: number
    percent: number
  }[]
  weekday_frequency: {
    day: string
    count: number
  }[]
  current_streak?: number
  longest_streak?: number
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
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
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
  const [moodFilter, setMoodFilter] = useState('')
  const [dateFromFilter, setDateFromFilter] = useState('')
  const [dateToFilter, setDateToFilter] = useState('')
  const [activeSection, setActiveSection] = useState('Jurnal')
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [remindersEnabled, setRemindersEnabled] = useState(false)
  const [reminderTime, setReminderTime] = useState('21:00')
  const reminderTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const monthLabel = useMemo(() => {
    return new Intl.DateTimeFormat('ro-RO', { month: 'long', year: 'numeric' }).format(currentMonth)
  }, [currentMonth])

  const pageTitle = activeSection === 'Dashboard' ? 'Dashboard' : 'Jurnalul meu'

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

      return matchesCategory
    })
  }, [activeCategory, mappedEntries])

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

  const loadEntries = useCallback(async (forUserId: number): Promise<void> => {
    const params = new URLSearchParams({ user_id: String(forUserId) })
    const search = searchTerm.trim()

    if (search) {
      params.set('search', search)
    }
    if (moodFilter) {
      params.set('mood', moodFilter)
    }
    if (dateFromFilter) {
      params.set('date_from', dateFromFilter)
    }
    if (dateToFilter) {
      params.set('date_to', dateToFilter)
    }

    const response = await fetch(`${API_BASE}/api/entries?${params.toString()}`)
    if (!response.ok) {
      const detail = (await response.json()) as { detail?: string }
      throw new Error(detail.detail ?? 'Nu am putut incarca intrarile din backend.')
    }
    const payload = (await response.json()) as ApiEntry[]
    setEntries(payload)
  }, [dateFromFilter, dateToFilter, moodFilter, searchTerm])

  const loadDashboardStats = useCallback(async (forUserId: number): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/dashboard?user_id=${forUserId}`)
    if (!response.ok) {
      const detail = (await response.json()) as { detail?: string }
      throw new Error(detail.detail ?? 'Nu am putut incarca dashboard-ul.')
    }
    const payload = (await response.json()) as DashboardStats
    setDashboardStats(payload)
  }, [])

  useEffect(() => {
    async function bootstrap(): Promise<void> {
      try {
        const userResponse = await fetch(`${API_BASE}/api/users/bootstrap`, { method: 'POST' })
        if (!userResponse.ok) {
          throw new Error('Nu am putut initializa utilizatorul demo.')
        }

        const userPayload = (await userResponse.json()) as { id: number; email: string }
        setUserId(userPayload.id)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Eroare necunoscuta de conectare la API.'
        setStatusMessage(message)
      } finally {
        setIsLoading(false)
      }
    }

    void bootstrap()
  }, [])

  useEffect(() => {
    async function loadSettings(): Promise<void> {
      if (!userId) return
      try {
        const resp = await fetch(`${API_BASE}/api/users/${userId}/settings`)
        if (!resp.ok) return
        const payload = await resp.json()
        setRemindersEnabled(Boolean(payload.reminders_enabled))
        if (payload.reminder_time) setReminderTime(payload.reminder_time)
      } catch {
        // ignore
      }
    }

    void loadSettings()
  }, [userId])

  // Show a native desktop notification (Electron / browser)
  function showDesktopNotification(title: string, body: string): void {
    try {
      if ('Notification' in window) {
        if (Notification.permission === 'granted') {
          new Notification(title, { body })
        } else if (Notification.permission !== 'denied') {
          void Notification.requestPermission().then((perm) => {
            if (perm === 'granted') {
              new Notification(title, { body })
            }
          })
        }
      }
    } catch (err) {
      // ignore errors
    }
  }

  // Schedule the next reminder based on `reminderTime` and `remindersEnabled`.
  function scheduleNextReminder(): void {
    // clear existing
    if (reminderTimerRef.current) {
      clearTimeout(reminderTimerRef.current)
      reminderTimerRef.current = null
    }

    if (!remindersEnabled || !reminderTime) return

    const [hh, mm] = reminderTime.split(':').map((s) => Number(s))
    if (Number.isNaN(hh) || Number.isNaN(mm)) return

    const now = new Date()
    const next = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hh, mm, 0, 0)
    if (next.getTime() <= now.getTime()) {
      next.setDate(next.getDate() + 1)
    }

    const delay = next.getTime() - now.getTime()
    reminderTimerRef.current = setTimeout(() => {
      // Only notify if user hasn't written today
      const todayIso = toIsoDate(new Date())
      const hasToday = entries.some((e) => e.entry_date === todayIso)
      if (!hasToday) {
        showDesktopNotification('Reminder Smart Journal', "Nu întrerupe streak-ul! Scrie în jurnalul tău azi.")
      }
      // schedule next one
      scheduleNextReminder()
    }, delay)
  }

  // Re-schedule when settings or entries change
  useEffect(() => {
    scheduleNextReminder()
    return () => {
      if (reminderTimerRef.current) {
        clearTimeout(reminderTimerRef.current)
        reminderTimerRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [remindersEnabled, reminderTime, entries])

  useEffect(() => {
    if (!userId) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      setIsLoading(true)
      Promise.all([loadEntries(userId), loadDashboardStats(userId)])
        .catch((error) => {
          const message = error instanceof Error ? error.message : 'Eroare la filtrarea intrarilor.'
          setStatusMessage(message)
        })
        .finally(() => setIsLoading(false))
    }, 250)

    return () => window.clearTimeout(timeoutId)
  }, [loadDashboardStats, loadEntries, userId])

  function clearFilters(): void {
    setSearchTerm('')
    setMoodFilter('')
    setDateFromFilter('')
    setDateToFilter('')
    setActiveCategory('Toate intrarile')
    setStatusMessage('Filtrele au fost resetate.')
  }

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

      await Promise.all([loadEntries(userId), loadDashboardStats(userId)])
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

      await Promise.all([loadEntries(userId), loadDashboardStats(userId)])
      closeEntryForm()
      setStatusMessage('Intrarea a fost stearsa.')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Eroare la stergere.'
      setStatusMessage(message)
    } finally {
      setIsDeletingEntry(false)
    }
  }

  async function saveSettings(): Promise<void> {
    if (!userId) return
    try {
      const resp = await fetch(`${API_BASE}/api/users/${userId}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reminders_enabled: remindersEnabled, reminder_time: reminderTime }),
      })
      if (!resp.ok) {
        const detail = await resp.json()
        setStatusMessage(detail.detail ?? 'Eroare la salvarea setărilor.')
        return
      }
      setStatusMessage('Setările au fost salvate.')
      setIsSettingsOpen(false)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Eroare necunoscută.'
      setStatusMessage(message)
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

        <button
          className="category"
          style={{ marginTop: 12, background: '#f3f4f6' }}
          onClick={() => setIsSettingsOpen(true)}
        >
          ⚙️ Setări reminder
        </button>

        <article className="streak-card">
          <strong>{dashboardStats ? dashboardStats.current_streak ?? 0 : visibleEntries.length}</strong>
          <span>{dashboardStats ? 'zile consecutive' : 'intrari vizibile'}</span>
          {dashboardStats && (
            <small style={{ opacity: 0.95, marginTop: 6, display: 'block' }}>
              Record: {dashboardStats.longest_streak ?? 0}
            </small>
          )}
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
          <h1>{pageTitle}</h1>
          <div className="topbar-actions">
            {activeSection === 'Jurnal' && (
              <input
                type="search"
                placeholder="Cauta intrare..."
                aria-label="Cauta intrare"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            )}
            <button className="primary" onClick={openCreateEntryForm}>
              + Intrare noua
            </button>
          </div>
        </header>

        {activeSection === 'Jurnal' && (
          <section className="filter-panel" aria-label="Filtre jurnal">
            <label>
              <span>Dispozitie</span>
              <select value={moodFilter} onChange={(event) => setMoodFilter(event.target.value)}>
                <option value="">Toate</option>
                <option value="Calm">Calm</option>
                <option value="Neutral">Neutral</option>
                <option value="Anxious">Anxious</option>
              </select>
            </label>
            <label>
              <span>De la</span>
              <input
                type="date"
                value={dateFromFilter}
                onChange={(event) => setDateFromFilter(event.target.value)}
              />
            </label>
            <label>
              <span>Pana la</span>
              <input
                type="date"
                value={dateToFilter}
                onChange={(event) => setDateToFilter(event.target.value)}
              />
            </label>
            <button className="secondary" onClick={clearFilters} type="button">
              Reseteaza filtre
            </button>
          </section>
        )}

        {isLoading && <p className="status-line">Se incarca datele din backend...</p>}
        {!isLoading && statusMessage && <p className="status-line">{statusMessage}</p>}

        {isSettingsOpen && (
          <div className="modal-overlay">
            <div className="modal" role="dialog" aria-modal>
              <h2>Setări reminder</h2>
              <label style={{ display: 'block', marginTop: 8 }}>
                <input
                  type="checkbox"
                  checked={remindersEnabled}
                  onChange={(e) => setRemindersEnabled(e.target.checked)}
                />{' '}
                Activează reminder zilnic
              </label>
              <label style={{ display: 'block', marginTop: 8 }}>
                Ora preferată
                <input
                  type="time"
                  value={reminderTime}
                  onChange={(e) => setReminderTime(e.target.value)}
                  style={{ display: 'block', marginTop: 6 }}
                />
              </label>
              <div style={{ marginTop: 12 }}>
                <button className="primary" onClick={() => void saveSettings()}>
                  Salvează
                </button>
                <button className="secondary" onClick={() => setIsSettingsOpen(false)} style={{ marginLeft: 8 }}>
                  Anulează
                </button>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'Dashboard' && dashboardStats && (
          <section className="dashboard" aria-label="Dashboard jurnal">
            <div className="stat-grid">
              <article className="stat-card">
                <span>Total intrari</span>
                <strong>{dashboardStats.total_entries}</strong>
              </article>
              <article className="stat-card">
                <span>Luna curenta</span>
                <strong>{dashboardStats.current_month_entries}</strong>
              </article>
              <article className="stat-card">
                <span>Zile cu jurnal</span>
                <strong>{dashboardStats.writing_days}</strong>
              </article>
              <article className="stat-card">
                <span>Dispozitie principala</span>
                <strong>{dashboardStats.top_mood}</strong>
              </article>
              <article className="stat-card">
                <span>Streak curent</span>
                <strong>{dashboardStats.current_streak ?? 0}</strong>
              </article>
              <article className="stat-card">
                <span>Record streak</span>
                <strong>{dashboardStats.longest_streak ?? 0}</strong>
              </article>
            </div>

            <div className="dashboard-grid">
              <section className="dashboard-panel" aria-label="Distributie dispozitii">
                <div className="panel-heading">
                  <h2>Dispozitii</h2>
                  <span>{Math.round(dashboardStats.average_mood_confidence * 100)}% incredere medie</span>
                </div>
                <div className="mood-bars">
                  {dashboardStats.mood_distribution.length === 0 && (
                    <p className="empty-state">Nu exista intrari pentru statistici.</p>
                  )}
                  {dashboardStats.mood_distribution.map((item) => (
                    <div key={item.mood} className="metric-row">
                      <div className="metric-label">
                        <span>{item.mood}</span>
                        <strong>{item.count}</strong>
                      </div>
                      <div className="bar-track" aria-label={`${item.mood}: ${item.percent}%`}>
                        <span style={{ width: `${item.percent}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="dashboard-panel" aria-label="Frecventa scrierii">
                <div className="panel-heading">
                  <h2>Frecventa</h2>
                  <span>intrari pe zile</span>
                </div>
                <div className="weekday-chart">
                  {dashboardStats.weekday_frequency.map((item) => {
                    const maxCount = Math.max(...dashboardStats.weekday_frequency.map((day) => day.count), 1)
                    const height = Math.max((item.count / maxCount) * 100, item.count > 0 ? 12 : 4)

                    return (
                      <div key={item.day} className="weekday-column">
                        <div className="column-track">
                          <span style={{ height: `${height}%` }} />
                        </div>
                        <strong>{item.count}</strong>
                        <small>{item.day}</small>
                      </div>
                    )
                  })}
                </div>
              </section>
            </div>
          </section>
        )}

        <div className={`month-line ${activeSection === 'Dashboard' ? 'hidden' : ''}`}>
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

        <section className={`calendar ${activeSection === 'Dashboard' ? 'hidden' : ''}`} aria-label="Calendar jurnal">
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
