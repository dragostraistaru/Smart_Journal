import { useMemo, useState } from 'react'

import './App.css'

type Entry = {
  id: number
  day: number
  title: string
  time: string
  category: string
  tone: 'yellow' | 'orange' | 'blue' | 'pink' | 'violet' | 'red'
}

const dayNames = ['LUN', 'MAR', 'MIE', 'JOI', 'VIN', 'SAM', 'DUM']
const monthLabels = ['Martie 2026', 'Aprilie 2026', 'Mai 2026']

const entries: Entry[] = [
  { id: 1, day: 1, title: 'Daily Journal', time: '15:30', category: 'Scrie', tone: 'yellow' },
  { id: 2, day: 2, title: 'Daily Journal', time: '14:30', category: 'Scrie', tone: 'yellow' },
  { id: 3, day: 3, title: 'Morning Plan', time: '06:00', category: 'Meditatie', tone: 'orange' },
  { id: 4, day: 7, title: 'Morning Plan', time: '06:30', category: 'Meditatie', tone: 'orange' },
  { id: 5, day: 8, title: 'Daily Journal', time: '19:15', category: 'Scrie', tone: 'yellow' },
  { id: 6, day: 9, title: 'Objective Plan', time: '10:00', category: 'Obiectiv nou', tone: 'blue' },
  { id: 7, day: 10, title: 'Morning Plan', time: '07:00', category: 'Meditatie', tone: 'orange' },
  { id: 8, day: 11, title: 'Reflections', time: '21:00', category: 'Ganduri', tone: 'pink' },
  { id: 9, day: 13, title: 'Daily Journal', time: '16:45', category: 'Scrie', tone: 'yellow' },
  { id: 10, day: 14, title: 'Morning Plan', time: '06:30', category: 'Meditatie', tone: 'orange' },
  { id: 11, day: 15, title: 'Objective Plan', time: '09:30', category: 'Obiectiv nou', tone: 'blue' },
  { id: 12, day: 16, title: 'My Mystery Plan', time: '11:00', category: 'Push', tone: 'violet' },
  { id: 13, day: 17, title: 'Daily Journal', time: '18:00', category: 'Scrie', tone: 'yellow' },
  { id: 14, day: 20, title: 'Daily Journal', time: '20:00', category: 'Scrie', tone: 'yellow' },
  { id: 15, day: 21, title: 'Objective Plan', time: '08:30', category: 'Obiectiv nou', tone: 'blue' },
  { id: 16, day: 22, title: 'Daily Journal', time: '14:00', category: 'Scrie', tone: 'yellow' },
  { id: 17, day: 27, title: 'Checkpoint', time: '12:00', category: 'Verificare', tone: 'red' },
]

const monthCells = [
  23, 24, 25, 26, 27, 28, 1,
  2, 3, 4, 5, 6, 7, 8,
  9, 10, 11, 12, 13, 14, 15,
  16, 17, 18, 19, 20, 21, 22,
  23, 24, 25, 26, 27, 28, 29,
  30, 31, 1, 2, 3, 4, 5,
]

function App() {
  const [activeCategory, setActiveCategory] = useState('Toate intrarile')
  const [searchTerm, setSearchTerm] = useState('')
  const [activeSection, setActiveSection] = useState('Jurnal')
  const [monthIndex, setMonthIndex] = useState(0)

  const visibleEntries = useMemo(() => {
    return entries.filter((entry) => {
      const matchesCategory =
        activeCategory === 'Toate intrarile' || entry.title === activeCategory
      const matchesSearch =
        searchTerm.trim().length === 0 ||
        `${entry.title} ${entry.category} ${entry.time}`
          .toLowerCase()
          .includes(searchTerm.trim().toLowerCase())

      return matchesCategory && matchesSearch
    })
  }, [activeCategory, searchTerm])

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
          {['Toate intrarile', 'Daily Journal', 'Morning Plan', 'Reflections', 'Objective Plan'].map(
            (category) => (
              <button
                key={category}
                className={`category ${activeCategory === category ? 'active' : ''}`}
                onClick={() => setActiveCategory(category)}
              >
                {category}
              </button>
            ),
          )}
          <button
            className="category add"
            onClick={() => alert('In iteratia 1 asta e doar mock UI. Aici vei crea o categorie noua.')}
          >
            + Categorie noua
          </button>
        </nav>

        <article className="streak-card">
          <strong>14</strong>
          <span>zile consecutive</span>
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
            <button
              className="primary"
              onClick={() => alert('Aici vei deschide formularul de intrare noua.')}
            >
              + Intrare noua
            </button>
          </div>
        </header>

        <div className="month-line">
          <button
            aria-label="Luna anterioara"
            onClick={() => setMonthIndex((current) => Math.max(0, current - 1))}
          >
            ‹ prev.
          </button>
          <strong>{monthLabels[monthIndex]}</strong>
          <button
            aria-label="Luna urmatoare"
            onClick={() => setMonthIndex((current) => Math.min(monthLabels.length - 1, current + 1))}
          >
            next ›
          </button>
        </div>

        <section className="calendar" aria-label="Calendar martie 2026">
          {dayNames.map((name) => (
            <div key={name} className="head-cell">
              {name}
            </div>
          ))}

          {monthCells.map((day, index) => {
            const isCurrentMonth = index >= 6 && index < 37
            const dayEntries = visibleEntries.filter((entry) => entry.day === day && isCurrentMonth)

            return (
              <article key={`${day}-${index}`} className={`day-cell ${isCurrentMonth ? '' : 'muted'}`}>
                <span className="day-number">{day}</span>
                <div className="entry-stack">
                  {dayEntries.map((entry, cardIndex) => (
                    <div
                      key={entry.id}
                      className={`entry-card ${entry.tone}`}
                      style={{ animationDelay: `${cardIndex * 80}ms` }}
                      role="button"
                      tabIndex={0}
                      onClick={() =>
                        alert(`${entry.title}\n${entry.time} · ${entry.category}\nZiua ${entry.day}`)
                      }
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
      </main>
    </div>
  )
}

export default App
