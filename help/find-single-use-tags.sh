sqlite3 searchy.db "SELECT t.name FROM tags t JOIN link_tags lt ON t.id = lt.tag_id GROUP BY t.id HAVING COUNT(lt.link_id) = 1 ORDER BY t.name;" > output.txt
