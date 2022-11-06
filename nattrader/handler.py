
class Handler():

    def __init__(self):
        '''
        This class handles the response from tradier and decides the next course of action
        based on defined logic
        '''
        pass

    def check_response(self, res):
        if res.status_code == 200:
            return res.json()
        else:
            return 0


