FunPy
=======
**FunPy** makes functional programming in Python easy by using MacroPy to reduce
boilerplate.

FunPy currently has the following features:

- [Case Classes](#case-classes), also known as algebraic data types
- [Pattern Matching](#pattern-matching)
- [Tail-call Optimization](#tail-call-optimization)
- [Quick Lambdas](#quick-lambdas)

Case Classes
------------
```python
from macropy.macros.adt import macros, case

@case
class Point(x, y): pass

p = Point(1, 2)

print str(p)    #Point(1, 2)
print p.x       #1
print p.y       #2
print Point(1, 2) == Point(1, 2)
#True
```

[Case classes](http://www.codecommit.com/blog/scala/case-classes-are-cool) are classes with extra goodies:

- Nice `__str__` and `__repr__` methods autogenerated
- An autogenerated constructor
- Structural equality by default
- A Copy-constructor, for creating modified copies of instances

The reasoning being that although you may sometimes want complex, custom-built classes with custom features and fancy inheritance, very (very!) often you want a simple class with a constructor, pretty `__str__` and `__repr__` methods, and structural equality which doesn't inherit from anything. Case classes provide you just that, with an extremely concise declaration:

```python
@case
class Point(x, y): pass
```

As opposed to the equivalent class, written manually:

```python
class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "Point(" + self.x + ", " + self.y + ")"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not self.__eq__(other)
```

Whew, what a lot of boilerplate! This is clearly a pain to do, error prone to deal with, and violates [DRY](http://en.wikipedia.org/wiki/Don't_repeat_yourself) in an extreme way: each member of the class (`x` and `y` in this case) has to be repeated _6_ times, with loads and loads of boilerplate. It is also *buggy*, and will fail at runtime when the above example is run, so see if you can spot the bug in it! Given how tedious writing all this code is, it is no surprise that most python classes do not come with proper `__str__` or useful `__eq__` functions! With case classes, there is no excuse, since all this will be generated for you.

Case classes also provide a convenient *copy-constructor*, which creates a shallow copy of the case class with modified fields, leaving the original unchanged:

```python
a = Point(1, 2)
b = a.copy(x = 3)
print a #Point(1, 2)
print b #Point(3, 2)
```

Like any other class, a case class may contain methods in its body:

```python
@case
class Point(x, y):
    def length(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

print Point(3, 4).length() #5
```

or class variables. The only restrictions are that only the `__init__`, `__repr__`, `___str__`, `__eq__` methods will be set for you, and it may not manually inherit from anything. Instead of manual inheritence, inheritence for case classes is defined by _nesting_, as shown below:

```python
@case
class List():
    def __len__(self):
        return 0

    def __iter__(self):
        return iter([])

    class Nil:
        pass

    class Cons(head, tail):
        def __len__(self):
            return 1 + len(self.tail)

        def __iter__(self):
            current = self

            while len(current) > 0:
                yield current.head
                current = current.tail

print isinstance(Cons(None, None), List)    # True
print isinstance(Nil(), List)               # True

my_list = Cons(1, Cons(2, Cons(3, Nil())))
empty_list = Nil()

print my_list.head              # 1
print my_list.tail              # Cons(2, Cons(3, Nil()))
print len(my_list)              # 5
print sum(iter(my_list))        # 6
print sum(iter(empty_list))     # 0
```

This is an implementation of a singly linked [cons list](http://en.wikipedia.org/wiki/Cons), providing both `head` and `tail` ([LISP](https://en.wikipedia.org/wiki/LISP)'s `car` and `cdr`) as well as the ability to get the `len` or `iter` for the list.

As the classes `Nil` are `Cons` are nested within `List`, both of them get transformed into top-level classes which inherit from it. This nesting can go arbitrarily deep.

Overall, case classes are similar to Python's [`namedtuple`](http://docs.python.org/2/library/collections.html#collections.namedtuple), but on steroids (methods, inheritence, etc.), and provides the programmer with a much better experience.

Pattern Matching
----------------
One important thing you might want to do with case classes is match them against some patterns.
For example, suppose that you are writing a function to transform an AST.  You want to try to macro-expand
with-blocks which represent macro invocation, but not affect anything else.

The code for this without pattern matching might look something like:
```python
def expand_macros(node):
    if (isinstance(node, With) and isinstance(node.context_expr, Name)
        and node.context_expr.id in macros.block_registry:
        return macros.block_registry[node.context_expr.id](node)
    else:
        return node
```

With pattern matching (specifically, using the switch macro), we could instead write:

```python
def expand_macros(node):
    with switch(node):
        if With(Name(macro_name)):
            return macros.block_registry[macro_name](node)
        else:
            return node
```

Once you're used to this, it is much simpler both to read and to write,
and the benefits of pattern matching only grow as the matched data structures get more complex.

Here is another, more self-contained example of an implementation of a <a href="http://en.wikipedia.org/wiki/Fold_(higher-order_function)">
left fold</a> from functional programming:

```python
@case
class List:
    class Nil():
        pass

    class Cons(x, xs):
        pass

def foldl1(my_list, op):
    with switch(my_list):
        if Cons(x, Nil()):
            return x
        elif Cons(x, xs):
            return op(x, foldl1(xs, op))
```

The switch macro is actually just syntactic sugar for using the more general patterns macro.
`foldl1` is approximately desugared into the following, with one important
caveat: the bodies of the if statements are not subject to pattern matching,
in case you actually want to use bitshifts in your code.

```python
def foldl1(my_list, op):
    with patterns:
        tmp = my_list
        try:
            Cons(x, Nil()) << tmp
            return x
        except PatternMatchException:
            try:
                Cons(x, xs) << tmp
                return op(x, foldl1(xs, op))
            except PatternMatchException:
                pass
```

I think you can agree that the first version is much easier to read, and the
second version hasn't even been fully expanded yet!

It's also possible to do away with the if statements if you know what the structure 
of your input will be.  This also has the benefits of throwing an exception if your 
input doesn't match the expected form. 

```python
from macropy.macros.adt import macros, patterns

def area(rect):
    with patterns:
        Rect(Point(x1, y1), Point(x2, y2)) << rect
        return (x2 - x1) * (y2 - y1)
```

If the match fails, a `PatternMatchException` will be thrown.
```python
    # Throws a PatternMatchException
    area(Line(Point(1, 2), Point(3, 4)))
```

###Class Matching Details

When you pattern match `Foo(x, y)` against a value `Foo(3, 4)`, what happens behind the
scenes is that the constructor of `Foo` is inspected.  We may find that it takes
two parameters `a` and `b`.  We assume that the constructor then contains lines
like:
```python
self.a = a
self.b = b
```
(We don't have access to the source of Foo, so this is the best we can do).
Then `Foo(x, y) << Foo(3, 4)` is transformed roughly into

```python
tmp = Foo(3,4)
tmp_matcher = ClassMatcher(Foo, [NameMatcher('x'), NameMatcher('y')])
tmp_matcher.match(tmp)
x = tmp_matcher.getVar('x')
y = tmp_matcher.getVar('y')
```

In some cases, constructors will not be so standard.  In this case, we can use
keyword arguments to pattern match against named fields.  For example, an
equivalent to the above which doesn't rely on the specific implementation of th constructor is `Foo(a=x, b=y)
<< Foo(3, 4)`.  Here the semantics are that the field `a` is extracted from
`Foo(3,4)` to be matched against the simple pattern `x`.  We could also replace
`x` with a more complex pattern, as in `Foo(a=Bar(z), b=y) << Foo(Bar(2), 4)`.


###Custom Patterns
It is also possible to completely override the way in which a pattern is matched
by defining an `__unapply__` class method of the class which you are pattern
matching.  The 'class' need not actually be the type of the matched object, as
in the following example borrowed from Scala.  The `__unapply__` method takes as
arguments the value being matched, as well as a list of keywords.

The method should then return a tuple of a list of positional matches, and a
dictionary of the keyword matches.

```python
class Twice(object):
    @classmethod
    def __unapply__(clazz, x, kw_keys):
        if not isinstance(x, int) or x % 2 != 0:
            raise PatternMatchException()
        else:
            return ([x/2], {})

with patterns:
    Twice(n) << 8
    print n     # 4
```

Tail-call Optimization
-----------
We have also implemented a macro which will optimize away the stack usage of
functions which are actually implemented in a tail-recursive fashion.  This even
works for mutually recursive functions by using trampolining.

The 'hello world' of tail-recursive functions is a factorial function, so I'll
show that first.
```python
@tco
def fact(n, acc):
    if n == 0:
        return acc
    else:
        return fact(n-1, n * acc)

print fact(10000)  # doesn't stack overflow
```

More complicated mutually recursive examples also work too.
```python
from macropy.macros.tco import macros, tco

@tco
def odd(n):
if n < 0:
    return odd(-n)
elif n == 0:
    return False
else:
    return even(n - 1)

@tco
def even(n):
    if n == 0:
        return True
    else:
        return odd(n-1)

assert(even(100000))  # No stack overflow
```

Note that both `odd` and `even` were both decorated with `@tco`.  All functions
which would ordinarily use too many stack frames must be decorated.

###Trampolining
How is tail recursion implemented?  The idea is that if a function `f` would
return the result of a recursive call to some function `g`, it could instead
return `g`, along with whatever arguments it would have passed to `g`.  Then
instead of running `f` directly, we run `trampoline(f)`, which will call `f`,
call the result of `f`, call the result of that `f`, etc. until finally some
call returns an actual value.

A transformed (and simplified) version of the tail-call optimized factorial
would look like this
```python
def trampoline_decorator(func):
    def trampolined(*args):
        if not in_trampoline():
            return trampoline(func, args)
        return func(*args)
    return trampolined

def trampoline(func, args):
  _enter_trampoline()
  while True:
        result = func(*args)
        with patterns:
            if ('macropy-tco-call', func, args) << result:
                pass
            else:
                if ignoring:
                    _exit_trampoline()
                    return None
                else:
                    _exit_trampoline()
                    return result

@trampoline_decorator
def fact(n, acc):
    if n == 0:
        return 1
    else:
        return ('macropy-tco-call', fact, [n-1, n * acc])
```

Quick Lambdas
-------------
```python
from macropy.macros.quicklambda import macros, f, _

map(f%(_ + 1), [1, 2, 3])
#[2, 3, 4]

reduce(f%(_ + _), [1, 2, 3])
#6
```

Macropy provides a syntax for lambda expressions similar to Scala's [anonymous functions](http://www.codecommit.com/blog/scala/quick-explanation-of-scalas-syntax). Essentially, the transformation is:

```python
f%(_ + _) -> lambda a, b: a + b
```

where the underscores get replaced by identifiers, which are then set to be the parameters of the enclosing `lambda`. This works too:

```python
map(f%_.split(' ')[0], ["i am cow", "hear me moo"])
#["i", "hear"]
```

Quick Lambdas can be also used as a concise, lightweight, more-readable substitute for `functools.partial`

```python
import functools
basetwo = functools.partial(int, base=2)
basetwo('10010')
#18
```

is equivalent to

```python
basetwo = f%int(_, base=2)
basetwo('10010')
#18
```

Quick Lambdas can also be used entirely without the `_` placeholders, in which case they wrap the target in a no argument `lambda: ...` thunk:

```python
from random import random
thunk = f%random()
print thunk()
#0.5497242707566372
print thunk()
#0.3068253802774531
```

This reduces the number of characters needed to make a thunk from 7 to 2, making it much easier to use thunks to do things like emulating [by name parameters](http://locrianmode.blogspot.com/2011/07/scala-by-name-parameter.html). 

Credits
=======

*FunPy is very much a work in progress, for the [MIT](http://web.mit.edu/) class [6.945: Adventures in Advanced Symbolic Programming](http://groups.csail.mit.edu/mac/users/gjs/6.945/). Although it is constantly in flux, all of the examples with source code represent already-working functionality. The rest will be filled in over the coming weeks.*

The MIT License (MIT)

Copyright (c) 2013, Justin Holmgren, Li Haoyi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
