from frontend import ChessBoard, ChessFEUnicode
from pieces import Piece
from agents import Player
from typing import Type, List, Tuple

class ChessEngine:
    """The backend of the chess game. Encodes all of the chess rules."""
    def __init__(self):
        self._chess_board  = ChessBoard()
        self._piece_fn_map = {Piece.BPAWN:   self.pawn_move_implications,
                              Piece.BROOK:   self.rook_move_implications, 
                              Piece.BKNIGHT: self.knight_move_implications, 
                              Piece.BBISHOP: self.bishop_move_implications, 
                              Piece.BQUEEN:  self.queen_move_implications, 
                              Piece.BKING:   self.king_move_implications, 
                              Piece.WPAWN:   self.pawn_move_implications,
                              Piece.WROOK:   self.rook_move_implications, 
                              Piece.WKNIGHT: self.knight_move_implications, 
                              Piece.WBISHOP: self.bishop_move_implications, 
                              Piece.WQUEEN:  self.queen_move_implications, 
                              Piece.WKING:   self.king_move_implications}
        self._white = {Piece.WROOK, Piece.WKNIGHT, Piece.WBISHOP, 
                       Piece.WQUEEN, Piece.WKING, Piece.WPAWN}
        self._last_white_move = []
        self._last_black_move = []
        self._white_turn = None
        self._white_king_pos = 'e1'
        self._black_king_pos = 'e8'

    def move_implications(self, 
                          p1: str, 
                          p2: str, 
                          white_turn: bool) -> List[Tuple[str,str]]:
        """Computes the implications of a specified move

        Args:
            p1 (string): Position of piece to move
            p2 (string): Proposed movement position

        Returns:
            consequences (List[Tuple[str, str]]): A list of move consequences.
                A consequence can be of four types: a piece capture, a 
                movement, a promotion, or a check. A piece capture is encoded as a 
                (str, None) tuple where str specifies captured piece position. 
                Another type is a movement which is encoded as a 
                (str, str) tuple. A promotion is encoded as 
                a (None, str) tuple. Finally, a check is encoded as a 
                (None, None) tuple. If the consequences list is empty, this 
                implies that the move is not valid. 
        """
        consequences = []
        p1num, p1letter = self._chess_board.unpack_move_string(p1)
        p2num, p2letter = self._chess_board.unpack_move_string(p2)
        src_piece  = self._chess_board.board[p1num][p1letter]

        # Checking bounds of move indices
        bounds_correct  = ord(p1num)    <= ord('8') and ord(p1num)    >= ord('1')
        bounds_correct &= ord(p2num)    <= ord('8') and ord(p2num)    >= ord('1')
        bounds_correct &= ord(p1letter) <= ord('h') and ord(p1letter) >= ord('a')
        bounds_correct &= ord(p2letter) <= ord('h') and ord(p2letter) >= ord('a')

        # Checking that the player isn't attempting to move an empty piece
        non_empty = src_piece != Piece.EMPTY

        # Checking that the player only moves pieces belonging to his color
        color_correct  = white_turn and src_piece in self._white
        color_correct |= not white_turn and src_piece not in self._white

        # Checking that piece isn't moving to itself
        not_same = p1 != p2

        valid = bounds_correct and non_empty and color_correct and not_same

        if valid:
            self._white_turn = white_turn

            consequences = self._piece_fn_map[src_piece](p1, p2)

            # Important to store last move info for en passant
            if self._white_turn:
                # Check for check
                movements = filter(lambda item: item[0] is not None and item[1] is not None, consequences)
                for movement in movements:
                    print(f"source pos: {movement[1]}")
                    in_check_cons = self._piece_fn_map[src_piece](movement[1], self._black_king_pos)
                    print("in check consequences: ", in_check_cons)
                    captures = filter(lambda item: item[0] is not None and item[1] is None, in_check_cons)
                    captures = list(captures)
                    print("captures: ", captures)
                    print("len(list(captures)): ", len(captures))
                    if len(captures) > 0:
                        print("check")
                        consequences.append((None,None))
                
                self._last_white_move = consequences
            else:
                # Check for check
                movements = filter(lambda item: item[0] is not None and item[1] is not None, consequences)
                for movement in movements:
                    print(f"source pos: {movement[1]}")
                    in_check_cons = self._piece_fn_map[src_piece](movement[1], self._white_king_pos)
                    print("in check consequences: ", in_check_cons)
                    captures = filter(lambda item: item[0] is not None and item[1] is None, in_check_cons)
                    captures = list(captures)
                    print("captures: ", captures)
                    print("len(list(captures)): ", len(captures))
                    if len(captures) > 0:
                        print("check")
                        consequences.append((None,None))

                self._last_black_move = consequences

        print(self._last_white_move)
        print(self._last_black_move)

        print("consequences: ", consequences)

        return consequences

    def pawn_move_implications(self, p1: str, p2: str) -> List[Tuple[str,str]]:
        # Four special pawn mechanics:
        #   1) 1 or 2 forward if on starting position
        #   2) Diagonal captures
        #   3) En passant
        #   4) Promotion
        p1num, p1letter = self._chess_board.unpack_move_string(p1)
        p2num, p2letter = self._chess_board.unpack_move_string(p2)

        consequences = []

        diff = ord(p2num) - ord(p1num)
        dir_correct = self._white_turn and diff > 0
        dir_correct |= not self._white_turn and diff < 0

        # Only continue if attempted move is in correct direction
        if dir_correct:
            in_initial = not self._chess_board.has_moved(p1)
            dest_piece = self._chess_board.board[p2num][p2letter]
            dest_piece_empty = dest_piece == Piece.EMPTY

            # Checking if movement is diagonal
            if self._white_turn:
                diag_row = ord(p1num) == ord(p2num) - 1
            else:
                diag_row = ord(p1num) == ord(p2num) + 1

            diag_col = (ord(p1letter) == ord(p2letter) + 1)
            diag_col |= (ord(p1letter) == ord(p2letter) - 1)

            is_diag = diag_col and diag_row

            if dest_piece_empty:
                same_col = p1letter == p2letter

                # Checking for valid forward movement
                if same_col:
                    num_fwd = diff if self._white_turn else -diff

                    if same_col and num_fwd > 0:
                        if num_fwd == 1:
                            consequences.append((p1,p2))
                        elif in_initial and num_fwd == 2:
                            consequences.append((p1,p2))

                # Check for en passant
                if is_diag:
                    captured = self.en_passant(p2)
                    if captured is not None:
                        consequences.append((p1,p2))
                        consequences.append((captured,None))

            # Handling standard diagonal capture
            if not dest_piece_empty:
                # If diagonal, then capture piece!
                if is_diag:
                    consequences.append((p1,p2))
                    consequences.append((p2,None))

            # Checking rank in case of promotion
            promotion_eligible = p2num == '8' and self._white_turn
            promotion_eligible |= p2num == '1' and not self._white_turn
            if promotion_eligible and len(consequences) > 0:
                consequences.append((None,p2))

        return consequences

    def rook_move_implications(self, p1: str, p2: str) -> List[Tuple[str,str]]:
        p1num, p1letter = self._chess_board.unpack_move_string(p1)
        p2num, p2letter = self._chess_board.unpack_move_string(p2)

        consequences = []

        same_row = p1num == p2num
        same_col = p1letter == p2letter

        # Check if positions are in same row or column
        if same_row or same_col:
            obstructed = self.straight_is_obstructed(p1num, p1letter, p2num, p2letter)

            if not obstructed:
                # Dealing with source piece and destination piece validation
                source_piece = self._chess_board.board[p1num][p1letter]
                dest_piece = self._chess_board.board[p2num][p2letter]
                
                source_color = "white" if source_piece in self._white else "black"

                # If there is a piece in the destination position
                if dest_piece != Piece.EMPTY:
                    dest_color = "white" if dest_piece in self._white else "black"

                    if dest_color != source_color:
                        # Eliminate piece
                        consequences.append((p2,None))
                        consequences.append((p1,p2))
                
                else:
                    consequences.append((p1,p2))
                        
        return consequences

    def knight_move_implications(self, p1: str, p2: str) -> List[Tuple[str,str]]:
        p1num, p1letter = self._chess_board.unpack_move_string(p1)
        p2num, p2letter = self._chess_board.unpack_move_string(p2)

        consequences = []

        row_diff = abs(ord(p1num) - ord(p2num))
        col_diff = abs(ord(p1letter) - ord(p2letter))

        dest_piece = self._chess_board.board[p2num][p2letter]
        dest_piece_empty = dest_piece == Piece.EMPTY

        source_color = "white" if self._white_turn else "black"
        dest_color = "white" if dest_piece in self._white else "black"

        valid_move = row_diff == 1 and col_diff == 2
        valid_move |= row_diff == 2 and col_diff == 1

        if not dest_piece_empty:
            valid_move &= dest_color != source_color

        capture = not dest_piece_empty
        capture &= dest_piece not in self._white if self._white_turn else dest_piece in self._white

        if valid_move:
            consequences.append((p1,p2))
            if capture:
                consequences.append((p2,None))

        return consequences

    def bishop_move_implications(self, p1: str, p2: str) -> List[Tuple[str,str]]:
        p1num, p1letter = self._chess_board.unpack_move_string(p1)
        p2num, p2letter = self._chess_board.unpack_move_string(p2)

        consequences = []

        row_diff = ord(p2num) - ord(p1num)
        col_diff = ord(p2letter) - ord(p1letter)

        diagonal = abs(row_diff) == abs(col_diff)
        is_obstructed = self.diag_is_obstructed(p1num, p1letter, p2num, p2letter)

        if diagonal and not is_obstructed:
            dest_piece = self._chess_board.board[p2num][p2letter]
            dest_piece_empty = dest_piece == Piece.EMPTY

            if dest_piece_empty:
                consequences.append((p1,p2))
            else:
                capture = self._white_turn and dest_piece not in self._white
                capture |= not self._white_turn and dest_piece in self._white

                if capture:
                    consequences.append((p1,p2))
                    consequences.append((p2,None))

        return consequences

    def queen_move_implications(self, p1: str, p2: str) -> List[Tuple[str,str]]:
        p1num, p1letter = self._chess_board.unpack_move_string(p1)
        p2num, p2letter = self._chess_board.unpack_move_string(p2)

        consequences = []

        row_diff = ord(p2num) - ord(p1num)
        col_diff = ord(p2letter) - ord(p1letter)

        diagonal = abs(row_diff) == abs(col_diff)
        same_row = p1num == p2num
        same_col = p1letter == p2letter

        if diagonal:
            is_obstructed = self.diag_is_obstructed(p1num, p1letter, p2num, p2letter)
            if not is_obstructed:
                dest_piece = self._chess_board.board[p2num][p2letter]
                dest_piece_empty = dest_piece == Piece.EMPTY

                if dest_piece_empty:
                    consequences.append((p1,p2))
                else:
                    capture = self._white_turn and dest_piece not in self._white
                    capture |= not self._white_turn and dest_piece in self._white

                    if capture:
                        consequences.append((p1,p2))
                        consequences.append((p2,None))

        elif same_row or same_col:
            is_obstructed = self.straight_is_obstructed(p1num, p1letter, p2num, p2letter)
            if not is_obstructed:
                # Dealing with source piece and destination piece validation
                source_piece = self._chess_board.board[p1num][p1letter]
                dest_piece = self._chess_board.board[p2num][p2letter]
                
                source_color = "white" if source_piece in self._white else "black"

                # If there is a piece in the destination position
                if dest_piece != Piece.EMPTY:
                    dest_color = "white" if dest_piece in self._white else "black"

                    if dest_color != source_color:
                        # Eliminate piece
                        consequences.append((p2,None))
                        consequences.append((p1,p2))
                
                else:
                    consequences.append((p1,p2))

        return consequences

    def king_move_implications(self, p1: str, p2: str) -> List[Tuple[str,str]]:
        pass

    def straight_is_obstructed(self, p1n: str, p1l: str, p2n: str, p2l: str) -> bool:
        p1num, p2num, = ord(p1n), ord(p2n)
        p1char, p2char = ord(p1l), ord(p2l)

        obstructed = False

        same_row = p1num == p2num
        same_col = p1char == p2char

        if same_row:
            start = p1char if p1char < p2char else p2char
            stop = p2char if start == p1char else p1char
            for ckey in range(start+1, stop):
                col_key = chr(ckey)
                if self._chess_board.board[chr(p1num)][col_key] != Piece.EMPTY:
                    obstructed = True

        elif same_col:
            start = p1num if p1num < p2num else p2num
            stop = p2num if start == p1num else p1num
            for rkey in range(start+1, stop):
                row_key = chr(rkey)
                if self._chess_board.board[row_key][chr(p1char)] != Piece.EMPTY:
                    obstructed = True

        return obstructed

    def diag_is_obstructed(self, p1n: str, p1l: str, p2n: str, p2l: str) -> bool:
        p1num, p2num, = ord(p1n), ord(p2n)
        p1char, p2char = ord(p1l), ord(p2l)

        row_diff = p2num - p1num

        obstructed = False

        start_col = min(p1char, p2char)
        start_row = p1num if start_col == p1char else p2num
        stop_row = p2num if start_row == p1num else p1num

        row_pos = stop_row - start_row > 0
        for i in range(1,abs(row_diff)):
            if row_pos:
                row_key = chr(start_row + i)
                col_key = chr(start_col + i)
                if self._chess_board.board[row_key][col_key] != Piece.EMPTY:
                    obstructed = True
            else:
                row_key = chr(start_row - i)
                col_key = chr(start_col + i)
                if self._chess_board.board[row_key][col_key] != Piece.EMPTY:
                    obstructed = True

        return obstructed

    def en_passant(self, dest_pos: str) -> bool:
        """Checks for en passant.

        Args:
            dest_pos (str): The destination position of the capturing piece

        Returns:
            bool: True if en passant is valid and piece can be captured
        """
        en_passant_valid = False
        captured_piece = None
        p2num, p2letter = self._chess_board.unpack_move_string(dest_pos)
        move_detector = lambda item: item[0] is not None and item[1] is not None

        if self._white_turn:
            last_black_moves = list(filter(move_detector, self._last_black_move))
            if len(last_black_moves) == 1:
                last_black_move = last_black_moves[0]
                lb1num, lb1letter = self._chess_board.unpack_move_string(last_black_move[0])
                lb2num, lb2letter = self._chess_board.unpack_move_string(last_black_move[1])
                lb_piece = self._chess_board.board[lb2num][lb2letter]
                lb_same_col = lb1letter == lb2letter
                num_fwd = abs(ord(lb2num) - ord(lb1num))
                
                # Based on last move, could be eligible for en passant
                if num_fwd == 2 and lb_same_col and lb_piece == Piece.BPAWN:
                    en_passant_valid = ord(lb2num) == ord(p2num) - 1
                    en_passant_valid &= ord(lb2letter) == ord(p2letter)
                    if en_passant_valid:
                        captured_piece = self._chess_board.pack_move_string(lb2num, lb2letter)
        else:
            last_white_moves = list(filter(move_detector, self._last_white_move))
            if len(last_white_moves) == 1:
                last_white_move = last_white_moves[0]
                lw1num, lw1letter = self._chess_board.unpack_move_string(last_white_move[0])
                lw2num, lw2letter = self._chess_board.unpack_move_string(last_white_move[1])
                lw_piece = self._chess_board.board[lw2num][lw2letter]
                lw_same_col = lw1letter == lw2letter
                num_fwd = abs(ord(lw2num) - ord(lw1num))

                # Based on last move, could be eligible for en passant
                if num_fwd == 2 and lw_same_col and lw_piece == Piece.WPAWN:
                    en_passant_valid = ord(lw2num) == ord(p2num) + 1
                    en_passant_valid &= ord(lw2letter) == ord(p2letter)
                    if en_passant_valid:
                        captured_piece = self._chess_board.pack_move_string(lw2num, lw2letter)

        return captured_piece

    def remove_piece(self, pos: str) -> None:
        """Remove piece at specified position from game board.

        Args:
            pos (str): Position of piece to be removed
        """
        self._chess_board.remove_piece(pos)

    def make_move(self, p1: str, p2: str) -> None:
        """Moves a piece in the backend.

        Args:
            p1 (str): Source position
            p2 (str): Destination position
        """
        self._chess_board.move_piece(p1, p2)

    def promote(self, position: str, piece: Piece) -> None:
        """Promotes a piece to a new piece. Classically, for pawns.
        
        Args:
            position (str): The position of the piece to be promoted
            piece (Piece): The piece that will replace the old piece
        """
        self._chess_board.promote_piece(position, piece)

    @property
    def game_state(self):
        return self._chess_board


class ChessGame:
    """The actual chess game. A game is comprised of players (policies) and an engine (rules, state)."""
    def __init__(self, player_1: Type[Player], player_2: Type[Player]) -> None:
        # Specify players
        self._player_1, self._player_2 = player_1, player_2

        # Initialize the engine... vroom vroom
        self._backend = ChessEngine()

        # Initialize the frontend
        self._frontend = ChessFEUnicode(self._backend.game_state)
        self._frontend.display_state()
        self._white_turn = True

        # Specify captured pieces
        self._captured_pieces = []

    def move(self) -> None:
        is_valid = False

        while not is_valid:
            pos1, pos2 = self._frontend.player_turn(self._white_turn)
            consequences = self._backend.move_implications(pos1, pos2, self._white_turn)

            # If the number of consequences is nonzero, then valid move.
            is_valid = len(consequences) != 0

            if not is_valid:
                self._frontend.display_state()
                print("Move invalid, please try again\n")
        
        if is_valid:
            # In chess, there can only ever be one capture in a move, 
            # but this just allows us to be more general...
            captures  = filter(lambda item: item[0] is not None and item[1] is None, consequences)
            movements = filter(lambda item: item[0] is not None and item[1] is not None, consequences)
            promotions = filter(lambda item: item[0] is None and item[1] is not None, consequences)
            check = list(filter(lambda item: item[0] is None and item[1] is None, consequences))
            in_check = len(check) > 0

            # We apply captures before making moves.
            for capture in captures:
                col, row = list(capture[0])
                self._captured_pieces.append(self._backend.game_state.board[row][col])
                self._backend.remove_piece(capture[0])

            # Update internal state after command is verified. Note that 
            # when castling is applied, multiple moves are required in a 
            # single turn.
            for positions in movements:
                self._backend.make_move(positions[0], positions[1])

            for promotion in promotions:
                updated_piece = self._frontend.promotion(self._white_turn)
                self._backend.promote(promotion[1], updated_piece)

            # TODO: Clean this up; figure out what right thing to do is when in check.
            #       could maybe pass check in as an arg to make move. Then if not moving
            #       king out of check or eliminating threat, move invalid.
            if in_check:
                self._frontend.notify_check(self._white_turn)

            self._frontend.display_state()
            # print(self._captured_pieces)

        self._white_turn = not self._white_turn