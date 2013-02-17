#!/usr/bin/env python

import math
# If a secure random number generator is unavailable, exit with an
# error.
try:
    import Crypto.Random.random
    secure_random = Crypto.Random.random.getrandbits
except ImportError:
    import OpenSSL
    secure_random = lambda x: long(hexlify(OpenSSL.rand.bytes(x >> 3)), 16)

class DiffieHellman(object):
    """
    An implementation of the Diffie-Hellman protocol.
    This class uses the 1536-bit MODP Group (Group 5) from RFC 3526.
    """
    prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF

    max_challenge_count = 8

    def __init__(self, use_proper_generator = True):
        """
        Generate the public and private keys.
        """

        # Here is where the magic happens.

        if use_proper_generator:
            self.generator = 2
        else:
            self.generator = secure_random(100)

        self.privateKey = secure_random(100)
        self.publicKey = pow(self.generator, self.privateKey, self.prime)
        self.last_challenge = 0
        self.challenge_count = 0
        self.secret = None

    def genKey(self, otherKey):
        """
        Derive the shared secret, then hash it to obtain the shared key.
        """
        self.secret = pow(otherKey, self.privateKey, self.prime)

    def generateChallenge(self):
        random_number = secure_random(100)
        self.last_challenge = random_number
        return (random_number, self.respondToChallenge(random_number))

    def respondToChallenge(self, random_number):
        result = pow(self.secret, random_number, self.prime)
        return (result & 1)
    def checkChallengeAnswer(self, answer):
        if str(self.respondToChallenge(self.last_challenge)) == answer:
            self.challenge_count += 1
            return True
        return False
    def convinced_p(self):
        return self.challenge_count >= self.max_challenge_count


import json
class DHEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DiffieHellman):
            d = {'__diffie_hellman__': True,
                 'secret': obj.secret,
                 'challenge_count': obj.challenge_count,
                 'last_challenge': obj.last_challenge,
                 'privateKey': obj.privateKey,
                 'publicKey': obj.publicKey,
                 'generator': obj.generator
                 }
            return d
        return json.JSONEncoder.default(self, obj)

    def as_DiffieHellman(self, dct):
        if "__diffie_hellman__" in dct:
            dh                 = DiffieHellman()
            dh.secret          = dct['secret']
            dh.challenge_count = dct['challenge_count']
            dh.last_challenge  = dct['last_challenge']
            dh.privateKey      = dct['privateKey']
            dh.publicKey       = dct['publicKey']
            dh.generator       = dct['generator']
            return dh
        return dct
    def loads(self, string):
        return json.loads(string, object_hook = self.as_DiffieHellman)

def parse_command(statemachines, string):
        if len(string) < 2:
            return
        if string[0] == "start":
            the_other = string[1]
            # If the other one is in our bangset we use a proper
            # generator, otherwise we use a random generator
            statemachines[the_other] = DiffieHellman(the_other in bang_set)
            print "msg %s BWFP:PUBKEY_INIT %s" % ( the_other, hex(statemachines[the_other].publicKey))
        elif string[0] == "msg":
            if len(string) < 3:
                return
            the_other = string[1]
            cmd = string[2]
            if cmd == "BWFP:PUBKEY_INIT":
                if len(string) != 4:
                    return
                statemachines[the_other] = DiffieHellman(the_other in bang_set)
                print "msg %s BWFP:PUBKEY_COMPLETE %s" % ( the_other, hex(statemachines[the_other].publicKey))
                statemachines[the_other].genKey(long(string[3], 16))
            elif cmd == "BWFP:PUBKEY_COMPLETE":
                if len(string) != 4:
                    return
                if not statemachines[the_other]:
                    return
                statemachines[the_other].genKey(long(string[3], 16))
                (random_number, _) = statemachines[the_other].generateChallenge()
                print "msg %s BWFP:CHALLENGE %s" % ( the_other, hex(random_number))
            elif string[2] == "BWFP:CHALLENGE":
                if len(string) < 4:
                    return
                dh = statemachines[the_other]
                if dh == None:
                    return
                # msg nick CHALLENGE <NUMBER> [answer]
                if len(string) == 5:
                    answer = string[4]
                    if not dh.checkChallengeAnswer(answer):
                        print "msg %s BWFP failed with %s, so probably there is no mutual interest." % ( own_username, the_other )
                        print "msg %s BWFP:CHALLENGE 0 2" % ( the_other)
                        statemachines[the_other] = None
                        return

                challenge = long(string[3], 16)
                if dh.convinced_p():
                    print "msg %s I'm conviced that %s likes you." % (own_username, the_other)
                if challenge == 0:
                    return
                answer = dh.respondToChallenge(challenge)
                if dh.convinced_p():
                    random_number = 0
                else:
                    (random_number, _) = dh.generateChallenge()
                print "msg %s BWFP:CHALLENGE %s %d" % ( the_other, hex(random_number), answer)

if __name__=="__main__":
    import sys
    if len(sys.argv) < 3:
        print "usage: program <state_file> <own_username> <nickname> <nickname> ..."
        sys.exit(1)

    # Load the state
    statemachines = {}
    try:
        with open(sys.argv[1]) as fd:
            statemachines = DHEncoder().loads(fd.read())
    except:
        pass

    own_username = sys.argv[2]
    bang_set = set(sys.argv[3:])

    try:
        string = raw_input().split(" ")
        parse_command(statemachines, string)
    except RuntimeError:
        pass

    with open(sys.argv[1], "w+") as fd:
        fd.write(DHEncoder().encode(statemachines))
