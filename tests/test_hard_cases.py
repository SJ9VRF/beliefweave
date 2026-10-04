from pwm.engine import PersonalMemoryEngine

def test_third_party_statement_not_extracted(tmp_path):
 e=PersonalMemoryEngine(tmp_path/'x.db'); r=e.ingest('u','My friend says I love sushi.')
 assert not r['actions']

def test_explicit_correction(tmp_path):
 e=PersonalMemoryEngine(tmp_path/'x.db'); e.ingest('u','I love coffee.'); e.ingest('u',"No, that's wrong. I dislike coffee.")
 a=e.memories.list_active('u'); assert len(a)==1 and a[0].predicate=='dislikes' and a[0].user_verified
