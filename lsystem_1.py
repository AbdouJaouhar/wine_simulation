import turtle
from typing import *
from dataclasses import dataclass, field
import secrets


@dataclass
class GrapeLSystem:
    m: int = 5
    ns: List[int] = field(default_factory=list)
    l: float = 40
    rl: float = 1
    rr: float = 0.75
    alpha: float = 45

    def extract_rules(self, string):
        replacements = []
        for k, c in enumerate(string):
            if c == "A" and k < len(string)-1 and string[k+1] in ["r", "f", "e", "p"]:
                next_string = string[k:].split(")")[0]
                i = int(float(next_string[3:].split(',')[0]))

                if string[k+1] != "e" and string[k+1] != "p":
                    j = int((next_string[3:].split(',')[1]))

                if string[k+1] == "r":
                    if i == 1:
                        new_comand = f"Ae({int(j*self.rl)})"
                    if i > 1:
                        print(i)
                        new_comand = f"F({j})[//Ar({i-1}, {int(j*self.rl)})][+({self.alpha})Af({self.ns[i-2]}, {int(j*self.rl)})]"

                if string[k+1] == "f":
                    if i > 1:
                        new_comand = f"F({j})[//Af({i-1}, {int(j*self.rl)})][+({self.alpha})Ae({j*self.rl})]"
                    if i == 1:
                        new_comand = f"Ae({int(j*self.rl)})"

                if string[k+1] == "e":
                    new_comand = f"F({i})[Ap({int(i*self.rl)})][+({self.alpha})Ap({int(i*self.rl)})][-({self.alpha})Ap({int(i*self.rl)})]"

                if string[k+1] == "p":
                    new_comand = f"F({i})S({int(self.l*self.rr)})"

                replacements.append([k, k + len(next_string), new_comand])

        decalage = 0

        for replacement in replacements:
            start, end, new_comand = replacement
            length_diff = len(new_comand) - (end-start)

            before = string[:max(0, start+decalage)]
            after = string[min(end+decalage, len(string)):]

            string = before + new_comand + after

            decalage += length_diff

        return string

    def iterate(self, n_iter: int = 10):
        omega = f"Ar({self.m},{self.l})"

        for iteration in range(n_iter):
            print("\n"+str(iteration))
            omega = self.extract_rules(omega)
            print(omega)
        self.instructions = omega

    def draw(self, speed=1000):
        stack = []
        t = turtle.Turtle()
        wn = turtle.Screen()

        t.hideturtle()
        t.speed(speed)
        t.right(90)

        cursor = 0
        Fs = 0

        while cursor < len(self.instructions):
            char = self.instructions[cursor]
            temp_string = self.instructions[cursor:]
            if char == "F":
                Fs += 1
                rgba = '#'+secrets.token_hex(3)
                param = temp_string[2:].split(')')[0]
                t.forward(int(float(param)))
                if Fs < self.m:
                    t.dot(5, rgba)

            elif char == "/":
                pass
            elif char == "[":
                stack.append([t.pos(), t.heading()])

            elif char == "]":
                pos, head = stack.pop()
                t.penup()
                t.goto(pos)
                t.setheading(head)
                t.pendown()

            elif char == "+":
                param = int(float(temp_string[2:].split(')')[0]))
                t.right(param)
            elif char == "-":
                param = int(float(temp_string[2:].split(')')[0]))

                t.left(param)
            elif char == "S":
                param = int(float(temp_string[2:].split(')')[0]))
                t.fillcolor(rgba)
                t.begin_fill()
                t.circle(param/2)
                t.end_fill()

            cursor += 1

        wn.onkey(wn.bye, 'q')
        wn.listen()
        turtle.mainloop()
        pass


grappe = GrapeLSystem(m=3, ns=[1, 2])
grappe.iterate(n_iter=10)
grappe.draw()
