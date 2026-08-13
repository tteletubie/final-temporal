books = [
    ("1984", "Dystopian", "George Orwell", "1949"),
    ("Animal Farm", "Satire", "George Orwell", "1945"),
    ("Homage to Catalonia", "Memoir", "George Orwell", "1938"),
    ("Down and Out in Paris and London", "Memoir", "George Orwell", "1933"),
    ("Twenty Thousand Leagues Under the Sea", "Adventure", "Jules Verne", "1870"),
    ("Journey to the Center of the Earth", "Adventure", "Jules Verne", "1864"),
    ("Around the World in Eighty Days", "Adventure", "Jules Verne", "1873"),
    ("The Mysterious Island", "Adventure", "Jules Verne", "1875"),
    ("From the Earth to the Moon", "Science Fiction", "Jules Verne", "1865"),
    ("Five Weeks in a Balloon", "Adventure", "Jules Verne", "1863"),
    ("Michael Strogoff", "Adventure", "Jules Verne", "1876"),
    ("In Search of the Castaways", "Adventure", "Jules Verne", "1868"),
    ("A Floating City", "Adventure", "Jules Verne", "1871"),
    ("The Steam House", "Adventure", "Jules Verne", "1880"),
    ("The Begum's Fortune", "Adventure", "Jules Verne", "1879"),
    ("Facing the Flag", "Adventure", "Jules Verne", "1896"),
    ("The Diary of a Young Girl", "Biography", "Anne Frank", "1947"),
    ("Women Who Love Too Much", "Psychology", "Robin Norwood", "1985"),
    ("The Alchemist", "Fiction", "Paulo Coelho", "1988"),
    ("Brida", "Fiction", "Paulo Coelho", "1990"),
    ("Veronika Decides to Die", "Fiction", "Paulo Coelho", "1998"),
    ("Eleven Minutes", "Fiction", "Paulo Coelho", "2003"),
    ("The Pilgrimage", "Fiction", "Paulo Coelho", "1987"),
    ("By the River Piedra I Sat Down and Wept", "Fiction", "Paulo Coelho", "1994"),
    ("Manual of the Warrior of Light", "Fiction", "Paulo Coelho", "1997"),
    ("The Zahir", "Fiction", "Paulo Coelho", "2005"),
    ("The Witch of Portobello", "Fiction", "Paulo Coelho", "2006"),
    ("Aleph", "Fiction", "Paulo Coelho", "2010"),
    ("Adultery", "Fiction", "Paulo Coelho", "2014"),
    ("Hippie", "Fiction", "Paulo Coelho", "2018"),
    ("The Little Prince", "Fantasy", "Antoine de Saint-Exupéry", "1943"),
    ("Pride and Prejudice", "Romance", "Jane Austen", "1813"),
    ("Sense and Sensibility", "Romance", "Jane Austen", "1811"),
    ("Emma", "Romance", "Jane Austen", "1815"),
    ("Frankenstein", "Horror", "Mary Shelley", "1818"),
    ("Dracula", "Horror", "Bram Stoker", "1897"),
    ("The Picture of Dorian Gray", "Classic", "Oscar Wilde", "1890"),
    ("To Kill a Mockingbird", "Drama", "Harper Lee", "1960"),
    ("The Great Gatsby", "Classic", "F. Scott Fitzgerald", "1925"),
    ("Fahrenheit 451", "Dystopian", "Ray Bradbury", "1953"),
    ("The Catcher in the Rye", "Classic", "J.D. Salinger", "1951"),
    ("Don Quixote", "Classic", "Miguel de Cervantes", "1605"),
    ("One Hundred Years of Solitude", "Magical Realism", "Gabriel García Márquez", "1967"),
    ("Chronicle of a Death Foretold", "Novel", "Gabriel García Márquez", "1981"),
    ("Love in the Time of Cholera", "Novel", "Gabriel García Márquez", "1985"),
    ("The Metamorphosis", "Fiction", "Franz Kafka", "1915"),
    ("The Trial", "Fiction", "Franz Kafka", "1925"),
    ("Crime and Punishment", "Psychological Fiction", "Fyodor Dostoevsky", "1866"),
    ("The Brothers Karamazov", "Philosophical Fiction", "Fyodor Dostoevsky", "1880"),
    ("The Stranger", "Philosophical Fiction", "Albert Camus", "1942"),
    ("The Plague", "Philosophical Fiction", "Albert Camus", "1947"),
    ("The Old Man and the Sea", "Fiction", "Ernest Hemingway", "1952"),
    ("A Farewell to Arms", "War Novel", "Ernest Hemingway", "1929"),
    ("The Sun Also Rises", "Novel", "Ernest Hemingway", "1926"),
    ("Moby-Dick", "Adventure", "Herman Melville", "1851"),
    ("Little Women", "Classic", "Louisa May Alcott", "1868"),
    ("Jane Eyre", "Romance", "Charlotte Brontë", "1847"),
    ("Wuthering Heights", "Gothic Fiction", "Emily Brontë", "1847"),
    ("Great Expectations", "Classic", "Charles Dickens", "1861"),
    ("Oliver Twist", "Classic", "Charles Dickens", "1838"),
    ("A Tale of Two Cities", "Historical Fiction", "Charles Dickens", "1859"),
    ("David Copperfield", "Classic", "Charles Dickens", "1850"),
    ("The Hobbit", "Fantasy", "J.R.R. Tolkien", "1937"),
    ("The Lord of the Rings", "Fantasy", "J.R.R. Tolkien", "1954"),
    ("The Fellowship of the Ring", "Fantasy", "J.R.R. Tolkien", "1954"),
    ("The Two Towers", "Fantasy", "J.R.R. Tolkien", "1954"),
    ("The Return of the King", "Fantasy", "J.R.R. Tolkien", "1955"),
    ("Harry Potter and the Philosopher's Stone", "Fantasy", "J.K. Rowling", "1997"),
    ("Harry Potter and the Chamber of Secrets", "Fantasy", "J.K. Rowling", "1998"),
    ("Harry Potter and the Prisoner of Azkaban", "Fantasy", "J.K. Rowling", "1999"),
    ("Harry Potter and the Goblet of Fire", "Fantasy", "J.K. Rowling", "2000"),
    ("Harry Potter and the Order of the Phoenix", "Fantasy", "J.K. Rowling", "2003"),
    ("Harry Potter and the Half-Blood Prince", "Fantasy", "J.K. Rowling", "2005"),
    ("Harry Potter and the Deathly Hallows", "Fantasy", "J.K. Rowling", "2007"),
    ("Percy Jackson and the Lightning Thief", "Fantasy", "Rick Riordan", "2005"),
    ("The Sea of Monsters", "Fantasy", "Rick Riordan", "2006"),
    ("The Titan's Curse", "Fantasy", "Rick Riordan", "2007"),
    ("The Battle of the Labyrinth", "Fantasy", "Rick Riordan", "2008"),
    ("The Last Olympian", "Fantasy", "Rick Riordan", "2009"),
    ("The Hunger Games", "Dystopian", "Suzanne Collins", "2008"),
    ("Catching Fire", "Dystopian", "Suzanne Collins", "2009"),
    ("Mockingjay", "Dystopian", "Suzanne Collins", "2010"),
    ("Divergent", "Dystopian", "Veronica Roth", "2011"),
    ("Insurgent", "Dystopian", "Veronica Roth", "2012"),
    ("Allegiant", "Dystopian", "Veronica Roth", "2013"),
    ("The Fault in Our Stars", "Romance", "John Green", "2012"),
    ("Looking for Alaska", "Young Adult", "John Green", "2005"),
    ("Paper Towns", "Young Adult", "John Green", "2008"),
    ("The Book Thief", "Historical Fiction", "Markus Zusak", "2005"),
    ("Life of Pi", "Adventure", "Yann Martel", "2001"),
    ("The Kite Runner", "Historical Fiction", "Khaled Hosseini", "2003"),
    ("A Thousand Splendid Suns", "Historical Fiction", "Khaled Hosseini", "2007"),
    ("The Giver", "Dystopian", "Lois Lowry", "1993"),
    ("The Maze Runner", "Science Fiction", "James Dashner", "2009"),
    ("The Da Vinci Code", "Mystery", "Dan Brown", "2003"),
]

def seed_books(conn):
    with conn as conn:
        cursor = conn.cursor()
        before = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]

        for name, category, author, year in books:
            cursor.execute(
                """
                INSERT INTO books (name, category, author, year)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM books
                    WHERE name = ? AND author = ?
                )
                """, (name, category, author, year, name, author)
            )

        conn.commit()

        after = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    print(f"Books added: {after - before}")
    print(f"Total books: {after}")