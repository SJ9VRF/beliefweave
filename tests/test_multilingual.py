from pwm.engine import PersonalMemoryEngine

def test_multilingual_preferences_canonicalize(tmp_path):
 e=PersonalMemoryEngine(tmp_path/'x.db')
 e.ingest('es','Me gusta sushi.',context='food')
 e.ingest('fr',"J'aime ramen.",context='food')
 e.ingest('fa','من پاستا را دوست دارم',context='food')
 assert e.memories.list_active('es')[0].predicate=='likes'
 assert e.memories.list_active('fr')[0].predicate=='likes'
 assert e.memories.list_active('fa')[0].predicate=='likes'
