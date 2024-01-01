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
        sorted_taglets = sorted(self.taglets)
        return ', '.join(map(str, sorted_taglets))

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

    def __contains__(self, taglet) -> bool:
        return taglet in self.taglets

    def __iter__(self):
        return iter(self.taglets)


class Note:
    """A note is a card in its most raw form. It has a front_side, back_side and as many tags as necessary.
    Notes can be manipulated into different types of card types, such as Basic, Front&Back, Typing,
    and MultipleChoice. One note is one row in the table."""
    def __init__(self, front_side: str, back_side: str, *taglets):
        self.front_side = front_side
        self.back_side = back_side
        self.tag = Tag(*taglets)
        self.note_id = 0

    def __str__(self):
        return f'{self.front_side}, {self.back_side}, {self.tag}'

    def __eq__(self, other) -> bool:
        # Overrides == operator for class Note
        # Catches cases where object is not of type Note.
        if not isinstance(other, Note):
            # don't attempt to compare against unrelated types
            return NotImplemented
        if self.tag != other.tag:
            return False
        # If all above are true and the front_side and back_side fields match, the notes are equal.
        return (self.front_side == other.front_side) and (self.back_side == other.back_side)

    def has_note_id(self) -> bool:
        return bool(self.note_id)


class Database:
    """Database class is used to store notes and their related tags."""
    # All database calls should be handled within this class and not metered out to the record classes.

    class DatabaseContextManager:
        """Creates a context manager to be called within the Database class methods for easy cleanup.
        All query methods should be using this context manager internally."""
        def __init__(self, database_file):
            # initialize connection variable and store database file here
            self.database_file = database_file
            self.connection = None

        def __enter__(self):
            # Set up db connection here
            self.connection = sqlite3.connect(self.database_file)
            self.connection.execute('PRAGMA foreign_keys = ON;')
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            # either commit or rollback here and close db.connection
            # error handling here
            if exc_type is not None:
                print(f"Query failed due to: {exc_type}")
                self.connection.rollback()
            else:
                print("Committing Transaction")
                self.connection.commit()
            self.connection.close()

    def __init__(self, database_file):
        self.database_file = database_file
        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS notes (
                            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            front_side TEXT NOT NULL UNIQUE, 
                            back_side TEXT NOT NULL
                        );
                    ''')
            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS taglets (
                            taglet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            taglet_name TEXT NOT NULL UNIQUE
                        );
                    ''')
            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS note_tags (
                            note_tags_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            note_id INTEGER,
                            taglet_id INTEGER,
                            FOREIGN KEY(note_id) REFERENCES notes(note_id) ON DELETE CASCADE,
                            FOREIGN KEY(taglet_id) REFERENCES taglets(taglet_id)
                        );
                    ''')

    def insert_note(self, note: Note) -> int:
        """Inserts a note record into the database. Returns a note_id used to index the note in
        the database. Will return note_id=0 if something went wrong."""
        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            note_id = 0
            try:
                # Insert into notes table
                cursor.execute('''
                    INSERT INTO notes (front_side, back_side)
                    VALUES (?, ?);
                ''', (note.front_side, note.back_side))

                # Fetch the note_id for the inserted note
                note_id = cursor.lastrowid

                # Insert into taglets table for each taglet
                for taglet in note.tag:
                    try:
                        cursor.execute('''
                            INSERT INTO taglets (taglet_name)
                            VALUES (?);
                        ''', (taglet,))
                    except sqlite3.IntegrityError as e:
                        # Ignore if taglet already exists in database
                        pass

                    # Fetch the taglet_id for the inserted or existing taglet
                    cursor.execute('''
                        SELECT taglet_id FROM taglets WHERE taglet_name = ?;
                    ''', (taglet,))
                    result = cursor.fetchone()
                    if result is not None:
                        taglet_id = result[0]

                        # Insert into note_tags table
                        cursor.execute('''
                            INSERT INTO note_tags (note_id, taglet_id)
                            VALUES (?, ?);
                        ''', (note_id, taglet_id))
            except Exception as e:
                # TODO Add logic here to catch duplicate entries and provide user feedback
                print(e)
                raise
            else:
                print(f'Inserted record: {note}')
                return note_id

    def get_note_by_fields(self, front_side, connection=None) -> Note or None:
        """Retrieves a Note object from the database based on the front_side field. Can be used to find
        notes if the note_id field is unknown as front_side field is forced unique."""
        if not front_side:
            return None
        if not connection:
            with self.DatabaseContextManager(self.database_file) as db:
                return self.get_note_by_fields(front_side, db.connection)
        else:
            cursor = connection.cursor()
            try:
                cursor.execute('''
                    SELECT note_id, front_side, back_side 
                    FROM notes 
                    WHERE front_side = ?;
                ''', (front_side, ))
                note_id, front_side, back_side = cursor.fetchone()

                cursor.execute('''
                    SELECT taglets.taglet_name
                    FROM taglets
                    INNER JOIN note_tags ON note_tags.taglet_id = taglets.taglet_id
                    WHERE note_id = ?;
                ''', (note_id, ))
                new_taglets = set(cursor.fetchall())
            except Exception as e:
                print(e)
                raise
            else:
                new_note = Note(front_side, back_side, *new_taglets)
                new_note.note_id = note_id
                return new_note
            finally:
                cursor.close()

    def get_note_by_id(self, note_id: int, connection=None) -> Note or None:
        """Retrieves a note record in the database based on note_id. Note_id field will be filled in the returned
        object. If there is no note_id that is passed in, or if there is no existing record with the given note_id this
        method will return None."""
        # Proper work flow in meta script should be to call this method in order to find the origin
        # for a delete_note() or update_note() call.

        if not note_id:
            return None

        if connection:
            print("entering get_note_by_id 'else: connection exists'")
            cursor = connection.cursor()
            try:
                # Get front_side and back_side fields of the record matching note_id
                cursor.execute('''
                                SELECT front_side, back_side
                                FROM notes
                                WHERE note_id = ?;
                            ''', (note_id,))
                result = cursor.fetchone()

                if result is None:
                    # Handle the case where no record with the given note_id is found
                    return None

                # Create Note instance to be returned later
                new_front_side, new_back_side = result
                new_note = Note(new_front_side, new_back_side)
                new_note.note_id = note_id

                # Grab corresponding taglets, if any
                cursor.execute('''
                                SELECT taglets.taglet_name 
                                FROM taglets
                                INNER JOIN note_tags ON taglets.taglet_id = note_tags.taglet_id
                                WHERE note_tags.note_id = ?;
                            ''', (note_id,))
                taglets = cursor.fetchall()

                # Create list of only first element for every return from fetch call because
                # it returns tuples with a blank second element
                taglets = [_[0] for _ in taglets]
            except Exception as e:
                print(e)
                raise
            else:
                # Add tag to note
                if taglets:
                    new_note.tag = Tag(*taglets)
                    new_note.note_id = note_id
                return new_note
            finally:
                cursor.close()
        if not connection:
            print("entering get_note_by_id 'not connection'")
            with self.DatabaseContextManager(self.database_file) as db:
                connection = db.connection
                return self.get_note_by_id(note_id, connection)

    def delete_note_by_id(self, note_id: int):
        """Deletes a Note record based on note_id."""

        with self.DatabaseContextManager(self.database_file) as db:
            original_note = self.get_note_by_id(note_id)
            cursor = db.connection.cursor()
            try:
                cursor.execute('''
                    DELETE FROM note_tags
                    WHERE note_id = ?;
                ''', (note_id, ))
                cursor.execute('''
                    DELETE FROM notes
                    WHERE note_id = ?;    
                ''', (note_id, ))
            except Exception as e:
                print(e)
                raise
            else:
                print(f"Deleted: {original_note}")

    def delete_unused_taglets(self):
        """Deletes all taglets not referenced in the note_tags table. Returns a tuple containing
        all taglets deleted from the database at this method call."""

        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            try:
                # Get all unused taglets for reference later
                cursor.execute('''
                    SELECT * FROM taglets
                    WHERE NOT EXISTS (
                        SELECT 1 FROM note_tags
                         WHERE taglets.taglet_id = note_tags.taglet_id
                    );
                ''')
                result = cursor.fetchall()

                # Delete all unused taglets
                cursor.execute('''
                    DELETE FROM taglets
                    WHERE NOT EXISTS (
                        SELECT 1 FROM note_tags
                        WHERE note_tags.taglet_id = taglets.taglet_id
                    );
                ''')
            except Exception as e:
                print(e)
                raise
            else:
                taglet_ids, deleted_taglets = zip(*result)
                deleted_taglets = Tag(deleted_taglets)
                print(f'Deleted taglets: {deleted_taglets}')
                return deleted_taglets

    def update_note(self, original_note_id: int, replacement: Note):
        """Updates the Note fields front_side and back_side and associated taglets in the database to equal that of
        replacement argument."""

        with self.DatabaseContextManager(self.database_file) as db:
            connection = db.connection
            # Grab original note for later reference
            original_note = self.get_note_by_id(original_note_id, connection)
            cursor = db.connection.cursor()
            try:
                # Update the front_side and back_side fields for the note row
                cursor.execute('''
                    UPDATE notes
                    SET front_side = ?,
                        back_side = ?
                    WHERE note_id = ?;
                ''', (replacement.front_side, replacement.back_side, original_note_id))

                # Recreate tag object with old taglets in order to perform note-math
                original_tag = original_note.tag

                # check to see if any of the taglets in the replacement note are new
                add_tag = replacement.tag - original_tag
                self.add_tag_to_note(original_note_id, add_tag)

                # Check to see if any of the taglets need to be removed from original note_id
                del_tag = original_tag - replacement.tag
                self.remove_tag_from_note(original_note_id, del_tag)
            except sqlite3.IntegrityError as e:
                print(e)
                raise
            except Exception as e:
                print(e)
                raise

    def add_tag_to_note(self, original_note_id: int, add_tag: Tag, connection=None):
        """Adds all the tags included in the add_tag to the note's record."""

        if not connection:
            with self.DatabaseContextManager(self.database_file) as db:
                connection = db.connection
                self.add_tag_to_note(original_note_id, add_tag, connection)

        cursor = connection.cursor()

        try:
            # Grab all note_id, taglet_name pairs to compare
            cursor.execute('''
                            SELECT taglets.taglet_id, taglets.taglet_name
                            FROM taglets
                            INNER JOIN note_tags ON taglets.taglet_id = note_tags.taglet_id
                            WHERE note_tags.note_id = ?;
                        ''', (original_note_id,))
            result = cursor.fetchall()
            taglet_ids, taglet_names = zip(*result)
            taglet_ids = list(taglet_ids)
            taglet_names = list(taglet_names)

            # Compare taglets with old note-taglet pairs
            for taglet in add_tag:
                if taglet not in taglet_names:
                    # if taglet is new, insert it into taglets table
                    cursor.execute('''
                                    INSERT OR IGNORE INTO taglets (taglet_name)
                                    VALUES (?);
                                ''', (taglet,))
                    # Get taglet_id for new note-taglet pairs
                    cursor.execute('''
                                    SELECT taglet_id
                                    FROM taglets
                                    WHERE taglet_name = ?;
                                ''', (taglet,))
                    result = cursor.fetchone()
                    if result is not None:
                        taglet_id = result[0]

                        # Create new note-taglet pair in note_tags
                        cursor.execute('''
                                        INSERT INTO note_tags (note_id, taglet_id)
                                        VALUES (?, ?);
                                    ''', (original_note_id, taglet_id))
        except Exception as e:
            print(e)
            raise
        finally:
            cursor.close()

    def remove_tag_from_note(self, original_note_id: int, del_tag: Tag):
        """Removes all the taglets in a tag from the note's database record."""
        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            try:
                if del_tag:
                    for del_taglet in del_tag:
                        cursor.execute('''
                            DELETE FROM note_tags
                            WHERE note_tags.note_id = ? AND
                                  note_tags.taglet_id IN (
                                      SELECT taglets.taglet_id FROM taglets
                                      WHERE taglets.taglet_name = ?
                                  );
                        ''', (original_note_id, del_taglet))
                    # Commit changes if everything is successful
            except Exception as e:
                print(e)
                raise

    def _print_all_notes(self):
        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            cursor.execute('''
                SELECT * FROM notes;
            ''')
            print("All notes: ", cursor.fetchall())

    def _print_all_note_tags(self):
        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            cursor.execute('''
                SELECT note_tags_id, front_side, taglet_name 
                FROM note_tags
                INNER JOIN notes ON note_tags.note_id = notes.note_id
                INNER JOIN taglets ON note_tags.taglet_id = taglets.taglet_id;    
            ''')
            print("All note_tags: ", cursor.fetchall())

    def _print_all_tags(self):
        with self.DatabaseContextManager(self.database_file) as db:
            cursor = db.connection.cursor()
            cursor.execute('''
                SELECT * FROM taglets;
            ''')
            print("All taglets: ", cursor.fetchall())
