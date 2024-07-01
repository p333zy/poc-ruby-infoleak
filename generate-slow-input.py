import time
import enum
import socket
import string
import random 

# seed = 0xd3adb33f
# random.seed(seed)

CHARACTERS = string.ascii_letters + string.digits

class Input(enum.Enum):
    PARENS_OPEN = 1
    PARENS_CLOSE = 2
    STAR = 3
    CHAR = 4
    LIST = 5
    PLUS = 6
    OPTIONAL = 7
    OR = 8
    ANY = 9

class State(enum.Enum):
    BEGIN = 0
    VALUE = [Input.CHAR, Input.LIST, Input.ANY]
    OPEN_PAREN = [Input.PARENS_OPEN]
    CLOSE_PAREN = [Input.PARENS_CLOSE]
    QTF = [Input.STAR, Input.PLUS]
    OPTIONAL = [Input.OPTIONAL]
    OR = [Input.OR]
    END = -1

STATE_TRANSITIONS = {
    State.BEGIN: [State.VALUE, State.OPEN_PAREN],
    State.VALUE: [State.VALUE, State.OPEN_PAREN, State.CLOSE_PAREN, State.QTF, State.OPTIONAL, State.OR],
    State.OPEN_PAREN: [State.VALUE, State.CLOSE_PAREN],
    State.CLOSE_PAREN: [State.VALUE, State.CLOSE_PAREN, State.QTF, State.OPTIONAL, State.OR],
    State.QTF: [State.VALUE, State.OPEN_PAREN, State.CLOSE_PAREN],
    State.OPTIONAL: [State.VALUE, State.OPEN_PAREN, State.CLOSE_PAREN, State.OR],
    State.OR: [State.VALUE, State.OPEN_PAREN],
    State.END: [State.END],
}

class RegexGenerator:
    def __init__(self, nchoices):
        self.nchoices = nchoices
        self.state = State.BEGIN
        self.last_state = State.BEGIN
        self.open_parens = 0
        self.cchoices = 0

    def next_state(self, from_state):
        self.last_state = from_state
        self.cchoices += 1

        if self.cchoices < self.nchoices:
            self.state = random.choice(STATE_TRANSITIONS[from_state])
        else:
            self.state = State.END

        # print(f'[+] Transitioned from {self.last_state} to {self.state}')

    def handle_begin(self):
        raise AssertionError('BEGIN should never be reached')

    def handle_value(self):
        value = random.choice(State.VALUE.value)

        match value:
            case Input.CHAR:
                return random.choice(CHARACTERS)
            case Input.LIST:
                chars = ''.join(random.choices(CHARACTERS, k=random.randint(2, 4)))
                return f'[{chars}]'
            case Input.ANY:
                return '.'

        raise AssertionError(f'Unhandled input type: {value}')

    def handle_parens_open(self):
        if self.last_state == State.OPEN_PAREN:
            self.next_state(State.VALUE)
            return self.handle_value()

        self.open_parens += 1
        return '('
        
    def handle_parens_close(self):
        # We don't allow empty parens

        if self.last_state == State.OPEN_PAREN:
            self.next_state(State.VALUE)
            return self.handle_value()

        if self.open_parens > 0:
            self.open_parens -= 1
            return ')'
        
        # If there aren't any open parens, we'll start a new group
        self.next_state(State.OPEN_PAREN)
        return self.handle_parens_open()

    def handle_qtf(self):
        value = random.choice(self.state.value)

        match value:
            case Input.PLUS:
                return '+'
            case Input.STAR:
                return '*'

    def handle_optional(self):
        return '?'
    
    def handle_or(self):
        return '|'

    def handle_end_with_or(self):
        self.last_state = State.VALUE
        return self.handle_value()

    def handle_end_with_open_parens(self):
        assert self.open_parens > 0
        self.last_state = State.VALUE
        self.open_parens -= 1
        return ')'

    def handle_end(self):
        if self.last_state == State.OR:
            return self.handle_end_with_or()

        if self.open_parens > 0:
            return self.handle_end_with_open_parens()

        raise StopIteration()

    def next_choice(self):
        self.next_state(self.state)

        match self.state:
            case State.VALUE:
                return self.handle_value()
            case State.OPEN_PAREN:
                return self.handle_parens_open()
            case State.CLOSE_PAREN:
                return self.handle_parens_close()
            case State.QTF:
                return self.handle_qtf()
            case State.OPTIONAL:
                return self.handle_optional()
            case State.OR:
                return self.handle_or()
            case State.END:
                return self.handle_end()
            
        return AssertionError(f'Unhandled state: {self.state}')

    def __iter__(self):
        self.cchoices = 0
        self.state = State.BEGIN
        self.last_state = State.BEGIN
        self.open_parens = 0
        return self

    def __next__(self):
        return self.next_choice()


def generate_slow_regex(nchoices):
    return ''.join(list(RegexGenerator(nchoices)))


sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.connect(('::1', 1234))

def send_input(regex):
    t0 = time.time()
    sock.send((regex + '\n').encode('ascii'))
    line = sock.recv(0x10)
    t1 = time.time()
    elapsed = t1 - t0
    print(f'[<] time {elapsed}')
    return elapsed

while True:
    input_len = random.randint(8, 0x10)
    regex = generate_slow_regex(input_len)

    print(f'[>] Sending regex: {regex}')
    elapsed = send_input(regex)

    if elapsed < 1:
        continue 

    print(f'[+] Very slow regex found: {regex}')

    if elapsed > 2.5:
        print('[-] Skipping since it is over 5 seconds')
        continue

    print(f'[/] retrying...')
    elapsed = send_input(regex)

    if elapsed > 1:
        print(f'[+] Very slow regex confirmed: {regex}')
        break 
