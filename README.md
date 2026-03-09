# Smart Journal

O aplicatie desktop de jurnal personal cu functionalitati AI pentru analiza dispozitiei si generarea de rezumate.

## Functionalitati

- **UC-1** Creare intrare in jurnal — cu detectie automata a dispozitiei prin BERT
- **UC-2** Editare intrare in jurnal — cu reanaliza dispozitiei daca textul s-a modificat
- **UC-3** Stergere intrare din jurnal
- **UC-4** Cautare si filtrare intrari — dupa cuvinte cheie, taguri, dispozitie, interval de date
- **UC-5** Vizualizare dashboard si statistici — grafice de dispozitie si frecventa scrierilor
- **UC-6** Generare rezumat lunar prin LLM
- **UC-7** Detectare tipare comportamentale prin LLM
- **UC-8** Urmarire streak de scriere
- **UC-9** Notificari reminder zilnice
- **UC-10** Export intrari in format PDF sau CSV
- **UC-11** Gestionare poze atasate intrarilor

## Roluri

| Rol | Descriere |
|-----|-----------|
| Utilizator | Actorul principal. Creeaza, editeaza, sterge si vizualizeaza intrari, acceseaza dashboard-ul si functiile AI. |
| Mood Detection Service (BERT) | Modul AI local care analizeaza textul si detecteaza dispozitia. Folosit in UC-1 si UC-2. |
| LLM Service | Serviciu de generare text folosit pentru rezumate lunare (UC-6) si detectarea tiparelor comportamentale (UC-7). |
| Notification System | Trimite reminder-e zilnice utilizatorului daca nu a scris o intrare in ziua respectiva (UC-9). |

## Stack tehnic

- **Limbaj**: Python
- **Interfata**: PyQt6
- **Baza de date**: ORM (SQLAlchemy)
- **AI — Mood detection**: BERT fine-tuned pe dataset de emotii
- **AI — Text generation**: LLM Service (Ollama local sau cloud facultate)
