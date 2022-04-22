import os
import requests
#import js2py


class PassCulture:
    def __init__(self):
        self.backend = "https://backend.passculture.app/native/v1"
        self.backend_headers = {
            "accept-encoding": "gzip"
        }

        self._algolia = "https://e2ikxj325n-dsn.algolia.net/1/indexes/*/queries" #?x-algolia-agent=Algolia%20for%20JavaScript%20(4.11.0)%3B%20Browser"
        self.algolia = "https://e2ikxj325n-3.algolianet.com/1/indexes/PRODUCTION/query" #?x-algolia-agent=Algolia%20for%20JavaScript%20(4.11.0)%3B%20Browser"
        self.algolia_headers = {
            "accept-encoding": "gzip",
            "content-type": "application/x-www-form-urlencoded",
            "x-algolia-api-key": "5743d3e703bf3aade8da0b12e8f67fb9",
            "x-algolia-application-id": "E2IKXJ325N"
        }

        self.user_agent = "Mozilla/5.0 (Linux; Android 5.1.1; PULP 4G Build/LMY47V; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/95.0.4638.74 Mobile Safari/537.36"

        self.s  = requests.Session()
        self.s.headers = {
            "user-agent": "ghrlt/passculture-private-api"
        }

        self.settings = self.back_settings()
        self.storage = "https://storage.googleapis.com"
        self._storage = self.settings['objectStorageUrl']
        
        self.subcategories = self.get_subcategories()

        self.is_logged_in = False 


    def force_login(self, authorization_token: str, refresh_token: str) -> bool:
        self.s.headers['authorization'] = "Bearer " + authorization_token
        r = self.s.get(f"{self.backend}/me")

        if r.status_code == 200:
            self.access_token = authorization_token
            self.refresh_token = refresh_token

            self.is_logged_in = True
            return True

        elif r.status_code == 401:
            r = r.json()
            if r.get('msg') == "Token has expired":
                # Try to use refresh token

                self.s.headers['authorization'] = "Bearer " + refresh_token
                r = self.s.post(f"{self.backend}/refresh_access_token").json()

                if r.get('accessToken'):
                    self.access_token =  r.get('accessToken')
                    self.refresh_token = refresh_token

                    self.s.headers['authorization'] = "Bearer " + self.access_token

                    self.is_logged_in = True
                    return True

                else:
                    return False

        raise Exception("Unhandled status code returned")

    def login(self, email: str, password: str) -> bool:
        h = {**self.backend_headers}
        h['content-type'] = "application/json"

        r = self.s.post(
            f"{self.backend}/signin",
            json={
                "identifier": email,
                "password": password
            },
            headers=h
        ).json()

        if r.get('accessToken'):
            self.refresh_token = r['refreshToken']
            self.access_token = r['accessToken']

            self.s.headers['authorization'] = "Bearer " + self.access_token

            self.is_logged_in = True

            with open('secrets', 'w') as f:
                f.write(self.access_token+'\n'+self.refresh_token)

            return True

        else:
            print(f"Problem in {list(r.keys())}: {list(r.values())}")

            self.is_logged_in = False
            return False


        #{'identifier': ['Ce champ est obligatoire']}
        #{'general': ['Identifiant ou Mot de passe incorrect']}
        #{'refreshToken': 'eyJ0eXAiOi...NiJ9.eyJmcmVza...4NX0.m72Tvf8u...vCiEQ', 'accessToken': 'eyJ0eXA...1NiJ9.eyJmcmVz...zg4fX0.4kkTZx...FdMUKA-GL25N9YE-oASJ1KVM'}
    
    def _register(self, email: str, password: str, birthdate: str, **kwargs) -> bool:
        h = {**self.backend_headers}
        h['content-type'] = "application/json"

        '''
        # Captcha token - Most likely impossible emulate a device (and even, it would require to fill the captcha sometimes)..
        r = requests.get(
            "https://www.google.com/recaptcha/api.js?hl=fr",
            headers={
                "accept-encoding": "gzip, deflate",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "referer": "https://passculture.app",
                "sec-fetch-dest": "script",
                "sec-fetch-mode": "no-cors",
                "sec-fetch-site": "cross-site",
                "user-agent": self.user_agent,
                "x-requested-with": "app.passculture.webapp"
            }
        ).text

        res = js2py.eval_js(r) #Warning: js2py has a pyimport statement that let's you run arbitrary code.
        #js2py.internals.simplex.JsException: ReferenceError: document is not defined
        '''

        captcha_token = "censored"
        
        r = self.s.post(
            f"{self.backend}/account",
            json={
                "email": email,
                "marketingEmailSubscription": kwargs.get('sub_to_marketing_emails') or False,
                "password": password,
                "birthdate": birthdate,
                "postalCode": "",
                "token": captcha_token
            }
        )
        return r.content


        #{"token":"The given token is not valid"}
        #{"token":["Le token renseign\\u00e9 n\'est pas valide"]} #token expiré
        #{"password":["Ce champ est obligatoire"]}
        #{"birthdate":["invalid date format"]}


    def back_settings(self) -> dict:
        r = self.s.get(f"{self.backend}/settings").json()
        return r


    def get_subcategories(self) -> dict:
        r = self.s.get(f"{self.backend}/subcategories").json()
        return r['subcategories']


    def get_offer(self, offer_id: int) -> dict:
        r = self.s.get(f"{self.backend}/offer/{offer_id}").json()
        return r

    def get_offers(self, hits: int, min_price: int=0, max_price: int=300) -> dict:
        # Feel free to make a more precize "get_offers" function and PR ;)

        _data = {
          "requests": [
                {
                  "indexName": "PRODUCTION",
                  "query": "",
                  "params": f'hitsPerPage={hits}'
                            '&facetFilters=[["offer.isEducational: false"],["offer.tags: 22bps16m"]]'
                            f'&numericFilters=[["offer.prices: {min_price}TO{max_price}"]]'
                            '&attributesToHighlight=[]'
                            '&attributesToRetrieve=['
                                '"offer.dates","offer.isDigital","offer.isDuo",'
                                '"offer.isEducational","offer.name","offer.prices",'
                                '"offer.subcategoryId","offer.thumbUrl","objectID","_geoloc"'
                            ']'
                }
          ]
        }
        data = {
            "query": "",
            "page": 0,
            "hitsPerPage": hits,
            "facetFilters": [
                ["offer.isEducational:false"],
                ["offer.searchGroupName:CINEMA"]
            ],
            "numericFilters": [
                [f"offer.prices: {min_price} TO {max_price}"]
            ],
            "attributesToRetrieve": [
                "objectID",
                "offer.dates",
                "offer.isDigital",
                "offer.isDuo",
                "offer.isEducational",
                "offer.name",
                "offer.prices",
                "offer.subcategoryId",
                "offer.thumbUrl",
                "_geoloc"
            ],
            "attributesToHighlight": []
        }

        r = self.s.post(
            f"{self.algolia}",
            json=data,
            headers=self.algolia_headers
        ).json()

        return r


    """ Require being logged on """

    def get_me(self) -> dict:
        r = self.s.get(f"{self.backend}/me").json()
        return r

    def get_remaining_balance(self, in_euros=True) -> int:
        remaining = self.get_me()['domainsCredit']['all']['remaining']
        if in_euros:
            return remaining/100
        return remaining

    def edit_account_password(self, current_psw: str, new_psw: str) -> bool|tuple[bool,str]:
       # new_psw can be == current_psw, api is okay with that :shrug:
      
      
        r = self.s.post(
            f"{self.backend}/change_password",
            json={
                "currentPassword": current_psw,
                "newPassword": new_psw
            }
        )
        if r.status_code == 204:
            return True
        return False, r.content

    def edit_marketing_preferences(self, via_email: bool, via_push: bool=True) -> bool|tuple[bool,str]:
        r = self.s.post(
            f"{self.backend}/profile",
            json={
                "subscriptions": {
                    "marketingEmail": via_email,
                    "marketingPush": via_push #This one is not editable from apps :thinking:
                }
            }
        )
        if r.status_code == 200:
            return True
        return False, r.content


    def get_favorites(self, only_count: bool=False) -> int|list:
        if only_count:
            r = self.s.get(f"{self.backend}/me/favorites/count").json()
            return r.get('count')

        r = self.s.get(f"{self.backend}/me/favorites").json()
        return r.get('favorites')

    def add_to_favorite(self, offer_id: int) -> bool|tuple[bool,str]:
        # ID is offer id
        
        r = self.s.post(f"{self.backend}/me/favorites", json={"offerId": offer_id})
        if r.status_code == 200:
            return True
        return False, r.content

    def remove_from_favorite(self, favorite_id: int) -> bool|tuple[bool,str]:
        # favorite_id is not Offer ID.
        # It's the id key on a get_favorites favorite object
        # (I did not investigate to know how is it generated)
        
        r = self.s.delete(f"{self.backend}/me/favorites/{favorite_id}")
        if r.status_code == 204:
            return True
        return False, r.content


    def get_reservations(self) -> dict:
        r = self.s.get(f"{self.backend}/bookings").json()
        return r

    def book_offer(self, stock_id: int, quantity: int) -> bool|tuple[bool,str]:
        # stock_id is found in an offer object
        
        r = self.s.post(
            f"{self.backend}/bookings",
            json={"quantity": quantity, "stockId": stock_id}
        ).json()

        if r.get('bookingId'):
            return True
        return False, r

        #<Response [400]> b'{"code":"ALREADY_BOOKED"}\n'

    def cancel_reservation(self, reservation_id: int) -> bool|tuple[bool,str]:

        r = self.s.post(f"{self.backend}/bookings/{reservation_id}/cancel")
        if r.status_code == 204:
            return True
        return False, r.content



app = PassCulture()
if not "secrets" in os.listdir():
    with open('secrets', 'w') as f:
        f.write("\n")


with open('secrets', 'r') as f:
    secrets = f.read()

auth, refresh = secrets.split('\n')
if auth or refresh:
    app.force_login(auth, refresh)

if not app.is_logged_in:
    app.login('ur@mail.com', 'UrP4s5w0rD')

#print(app.get_me())
#print(app.get_remaining_balance())
#print(app.edit_account_password('currentpsw', 'newpsw'))
#print(app.edit_marketing_preferences(False, True))

#print(app.get_favorites(only_count=True))

#print(app.get_offer(59785571))
#print(app.book_offer( app.get_offer(59785571)['stocks'][0]['id'], quantity=1 ))
#print(app.cancel_reservation( app.get_reservations()['ongoing_bookings'][0]['id'] ))

#print(app.get_reservations())

#print(app.get_favorites())
#print(app.remove_from_favorite( app.get_favorites()[0]['id'] ))
#print(app.get_favorites(only_count=True))
