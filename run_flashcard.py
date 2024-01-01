from database import Database, Note, Tag
from gui import RootWindow

FLASHCARD_DB_PATH = 'flashcards.db'
#
# with RootWindow() as app:

flash_db = Database(FLASHCARD_DB_PATH)

note1 = Note('я', 'I', 'Pronouns', 'Nouns', 'Chapter1', 'Chapter3')
note2 = Note('ты', 'You', 'Pronouns')
note3 = Note('мы', 'We', 'Chapter1', 'Pronouns', 'Nouns', 'Chapter2')
note_upd1 = Note('яя', 'II', 'Pronouns', 'Nouns', 'Chapter1', 'test1')

note1.note_id = flash_db.insert_note(note1)
note2.note_id = flash_db.insert_note(note2)
note3.note_id = flash_db.insert_note(note3)

note1_copy = flash_db.get_note_by_id(note1.note_id)

# should remove chapter3 taglet and add test1 taglet
flash_db.update_note(note1.note_id, note_upd1)

flash_db.delete_note_by_id(note1.note_id)
flash_db.delete_note_by_id(note2.note_id)
flash_db.delete_note_by_id(note3.note_id)

flash_db.delete_unused_taglets()



