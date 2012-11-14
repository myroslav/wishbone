============
Introduction
============

Wishbone is a Python programming library to write `asynchronous` event pipelines mainly focussed on event processing.
It does this by connecting modules to each other by shoveling data from one module's queue into the other in order to create an event processing flow.
A module follows the Unix philosophy of writing programs that do one thing and do it well.  Modules work independently and asynchronously from each other without the need for callbacks.
WishBone is build upon the great Gevent library which uses the libevent library as an eventloop.

You can find documentation here:
	http://smetj.github.com/wishbone/index.html
