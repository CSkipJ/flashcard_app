import sqlite3


class Tag:
    """Tag class holds a set of taglets. Each taglet is used to further distinguish notes by
    subject/topic/chapter. Each Note can have multiple taglets, which allows users to easy filter notes/cards
    and create custom decks based on subjects."""

    def __init__(self, *taglets):
        self.taglets = set(taglets)

    def __eq__(self, other):
        # Overrides == operator for class Tag
        if not isinstance(other, Tag):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return self.taglets == other.taglets

    def __str__(self):
        return str(self.taglets)

    def __sub__(self, other):
        if not isinstance(other, Tag):
            # don't attempt to compare against unrelated types
            return NotImplemented
        new_tag = Tag()
        new_tag.taglets = self.taglets - other.taglets
        return new_tag

    def __add__(self, other):
        if not isinstance(other, Tag):
            # don't attempt to compare against unrelated types
            return NotImplemented
        new_tag = self
        new_tag.taglets.update(other.taglets)
        return new_tag

    def __iadd__(self, other):
        if not isinstance(other, Tag):
            # don't attempt to compare against unrelated types
            return NotImplemented
        self.taglets.update(other.taglets)
        return self

    def __isub__(self, other):
        if not isinstance(other, Tag):
            # don't attempt to compare against unrelated types
            return NotImplemented
        self.taglets = self.taglets - other.taglets
        return self

    def __bool__(self):
        if self.taglets:
            return True
        return False


class Note:
    """A note is a card in its most raw form. It has a front, back and as many tags as necessary.
    Notes can be manipulated into different types of card types, such as Basic, Front&Back, Typing,
    and MultipleChoice. One note is one row in the table."""
    def __init__(self, front: str, back: str, *taglets):
        self.front = front
        self.back = back
        self.tag = Tag(*taglets)

    def __str__(self):
        ret = ', '.join((self.front, self.back))
        return ret

    def __eq__(self, other):
        # Overrides == operator for class Note
        # Catches cases where object is not of type Note.
        if not isinstance(other, Note):
            # don't attempt to compare against unrelated types
            return NotImplemented
        if self.tag != other.tag:
            return False
        # If all above are true and the front and back fields match, the notes are equal.
        return (self.front == other.front) and (self.back == other.back)

    def compare(self, other) -> int:
        """Returns 0 if there are no differences between this note and the other,
        1 if the front field is different, and 2 if the back field is different."""
        # Catches cases where object is not of type Note.
        if not isinstance(other, Note):
            # don't attempt to compare against unrelated types
            return NotImplemented
        if self == other:
            return 0
        if self.front != other.front:
            return 1
        if self.back != other.back:
            return 2
        if self.tag != other.tag:
            return 3


class Database:
    """Database class is used to store notes."""

    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.connection.execute('PRAGMA foreign_keys = ON;')
        self.cursor = self.connection.cursor()
        self.commit_db()

        print("Creating notes table")
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notes (
                        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        front TEXT NOT NULL UNIQUE, 
                        back TEXT NOT NULL
                    );
                ''')

        print("Creating tags table")
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tags (
                        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag_name TEXT NOT NULL UNIQUE
                    );
                ''')

        print("Creating note_tags table")
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS note_tags (
                        note_tags_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        note_id INTEGER,
                        tag_id INTEGER,
                        FOREIGN KEY(note_id) REFERENCES notes(note_id) ON DELETE CASCADE,
                        FOREIGN KEY(tag_id) REFERENCES tags(tag_id)
                    );
                ''')
        self.commit_db()

    def insert_note(self, note: Note):
        self.connection.execute('PRAGMA foreign_keys = ON;')
        try:
            # Insert into notes table
            self.cursor.execute('''
                INSERT INTO notes (front, back)
                VALUES (?, ?);
            ''', (note.front, note.back))

            # Fetch the note_id for the inserted note
            note_id = self.cursor.lastrowid

            # Insert into tags table for each tag
            for tag in note.tag.taglets:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO tags (tag_name)
                    VALUES (?);
                ''', (tag,))

                # Fetch the tag_id for the inserted or existing tag
                self.cursor.execute('''
                    SELECT tag_id FROM tags WHERE tag_name = ?;
                ''', (tag,))
                tag_id = self.cursor.fetchone()[0]

                # Insert into note_tags table
                self.cursor.execute('''
                    INSERT INTO note_tags (note_id, tag_id)
                    VALUES (?, ?);
                ''', (note_id, tag_id))

            self.commit_db()

        except Exception as e:
            print(e)
        else:
            print(f'Inserted record for {note},')

    def delete_note(self, note: Note):
        try:
            self.cursor.execute('''
                SELECT notes.note_id, notes.front, note_tags.note_tags_id 
                FROM notes
                INNER JOIN note_tags ON notes.note_id = note_tags.note_id
                WHERE front = ?;
            ''', (note.front, ))

            row = self.cursor.fetchone()

            self.cursor.execute('''
                DELETE FROM note_tags
                WHERE note_tags_id = ?;
            ''', (row[2], ))

            self.cursor.execute('''
                DELETE FROM notes
                WHERE note_id = ?;
            ''', (row[0], ))
        except Exception as e:
            print(e)
        else:
            print(f"Deleted note: {row[1]}")

    def update_note(self, original: Note, replacement: Note):
        try:
            self.cursor.execute('''
                SELECT notes.front, notes.back, note_tags.tag_id
                FROM notes
                INNER JOIN note_tags ON notes.note_id = note_tags.note_id
                WHERE front = ? AND back = ?;
            ''', (original.front, original.back))
            front, back, tag_id = self.cursor.fetchone()
            print(f'retrieved for update -> front: {front}, back: {back}, tag_id: {tag_id}')
            self.cursor.execute('''
                SELECT tag_name FROM note_tags
                WHERE tag_id = ?;
            ''', (tag_id, ))
            tags = self.cursor.fetchall()
            print(tags)
        except Exception as e:
            print(e)
        else:
            print(f"Updated note: {original}")

        # TODO Finish method

    def update_tag(self):
        pass

    def _print_all_notes(self):
        self.cursor.execute('''
            SELECT * FROM notes;
        ''')
        print("All notes: ", self.cursor.fetchall())

    def _print_all_note_tags(self):
        self.cursor.execute('''
            SELECT note_tags_id, front, tag_name 
            FROM note_tags
            INNER JOIN notes ON note_tags.note_id = notes.note_id
            INNER JOIN tags ON note_tags.tag_id = tags.tag_id;    
        ''')
        print("All note_tags: ", self.cursor.fetchall())

    def _print_all_tags(self):
        self.cursor.execute('''
            SELECT * FROM tags;
        ''')
        print("All tags: ", self.cursor.fetchall())

    def commit_db(self):
        self.connection.commit()

    def close_db(self):
        self.connection.close()
