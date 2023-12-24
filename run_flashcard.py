from database import Database, Note, Tag

FLASHCARD_DB_PATH = 'flashcards.db'
flash_db = Database(FLASHCARD_DB_PATH)

note1 = Note('я', 'I', 'Pronouns', 'Nouns', 'Chapter1', 'Chapter3')
note2 = Note('ты', 'You', 'Pronouns')
note3 = Note('я', 'I', 'Chapter1', 'Pronouns', 'Nouns', 'Chapter2')
note_upd1 = Note('яя', 'II', 'Pronouns', 'Nouns', 'Chapter1')


# flash_db.insert_note(note1)
# flash_db.insert_note(note2)
#
# flash_db.update_note(note1, note_upd1)


# flash_db._print_all_notes()
# flash_db._print_all_note_tags()
# flash_db._print_all_tags()
# flash_db.delete_note(note1)
# flash_db._print_all_notes()
# flash_db._print_all_note_tags()
# flash_db._print_all_tags()

flash_db.close_db()
