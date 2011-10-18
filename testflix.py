from netflix import Netflix

NETFLIX_API_KEY = '4h4ptbdbuj2gf7pkpqsr2gmp'
NETFLIX_API_SECRET = 'p29dxQgr8M'
NETFLIX_APPLICATION_NAME = 'Test app'

flix = Netflix(key=NETFLIX_API_KEY,
                   secret=NETFLIX_API_SECRET,
                   application_name=NETFLIX_APPLICATION_NAME)

#test = flix.request('/catalog/titles', term='futurama', max_results = 10)
token = flix.get_request_token()

test = flix.request(url='/users/current/queues',
                    token=token,
                    verb='POST',
                    max_results = 10)
print test
