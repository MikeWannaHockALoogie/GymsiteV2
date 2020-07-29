class Board():
    def __init__(self, score=0, moves = []):
        self.state = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
        ]
        self.frontier = []
        self.score = score
        self.moves = moves

    def show(self):
        for row in board.state:
            print(row)

    def play(self, player, coordinates: tuple):
        x = coordinates[0]
        y = coordinates[1]
        self.state[x][y] = player.symbol

    def check_for_actions(self):
        board = self.state
        for x in range(len(board)):
            for y in range(len(board[x])):
                if not board[x][y]:
                    if (x, y) not in self.frontier:
                        self.frontier.append((x, y))
        return self.frontier

    def check_for_win(self):
        board = self.state
        for row in board:
            if row[0] == row[1] == row[2]:
                if row[0] == 'x':
                    self.score += 1
                    return True, 'player 1'
                    
                elif row[0] != None:
                    self.score += 1
                    return True, 'player 2'
                    

        for i in range(len(row)):
            if board[0][i] == board[1][i] == board[2][i]:
                if board[0][i] == 'x':
                    self.score += 1
                    return True, 'player 1'
                elif board[0][i] != None:
                    self.score -= 1
                    return True, 'player 2'
                    

        if board[0][0] == board[1][1] == board[2][2]:
            if board[0][0] == 'x':
                self.score += 1
                return True, 'player 1'                
            elif board[0][0] != None:
                self.score -= 1
                return True, 'player 2'

        if board[0][2] == board[1][1] == board[2][0]:
            if board[0][2] == 'x':
                self.score += 1
                return True, 'player 1'

            elif board[0][2] != None:
                self.score -= 1
                return True, 'player 2'

        else:
            return False
    
    def some():
        pass


class Player():
    def __init__(self, num):
        self.num = num
        self.moves = []
        if self.num == 1:
            self.symbol = 'x'
        else:
            self.symbol = 'y'

    def __str__(self):
        return f'player {self.num}'
    
    def ai(self, board, other):
        board.check_for_actions()
        action = board.frontier.pop(0)
        while action:
            max = 0
            if action == None:
                print('do something')
            board.moves.append(action)
            new_board = board.play(self, action)
            



class Game():
    def __init__(self, players: list, board):
        self.players = players
        self.board = board

    def play(self):

        while True:
            actions = []
            actions = board.check_for_actions()
            print(actions)
            action = actions.pop(0)
            board.play(player_1, action)
            board.show()
            print('')
            if board.check_for_win():
                print(board.check_for_win())
                break
            action = []
            actions = board.check_for_actions()
            print(actions)
            action = actions.pop(0)
            board.play(player_2, action)
            board.show
            print('')
            if board.check_for_win():
                print(board.check_for_win())
                break


player_1 = Player(1)
player_2 = Player(2)
board = Board()
game = Game([player_1, player_2], board)
game.play()
