/*
	Queχ Lexical Analyzer
*/
#include "Lexer"

/*
	International Components for Unicode (ICU)
*/
#include <unicode/unistr.h>
#include <unicode/uchar.h>
#include <unicode/uchriter.h>
#include <unicode/normlzr.h>
#include <unicode/schriter.h>
#include <unicode/uidna.h>
#include <unicode/uniset.h>

/*
	Standard C++ Library
*/
#include <cstdlib>
#include <cstdio>
#include <cstring>

#include <fstream>
#include <iostream>
#include <sstream>

/*
	C++ Standard Template Library (STL)
*/
#include <bitset>
#include <queue>
#include <deque>
#include <stack>
#include <vector>

using namespace std;
using namespace quex;

namespace quex {
	class Parser {
		protected:
			const std::string filePath;
			Lexer lexer;
			stack<deque<Token *> *> tokenMemento;
			deque<Token *> tokenQueue;

		public:
			/* ?! */ Parser(const std::string & fileName, const char * encoding = 0x00, bool byteOrderReversionFlag = false);
			virtual ~Parser();

		public:
			virtual void parse();
			virtual void assemble();
			virtual void write();

		protected:
			virtual Token * read();
			virtual Token * peek();
			virtual Token * peek(unsigned long int peekIndex);

			virtual bool markPosition();
			virtual bool backtrack();
			virtual bool omitPosition();
	};

	Parser::Parser(const std::string & fileName, const char * encoding, bool byteOrderReversionFlag) : filePath(fileName), lexer(fileName,encoding), tokenMemento(), tokenQueue() {
		tokenMemento.push(new deque<Token *>());
	}

	Parser::~Parser() {
		deque<Token *> * memento;

		while(!tokenMemento.empty()) {
			memento = tokenMemento.top();

			// Remove first...
			tokenMemento.pop();

			while(!memento->empty()) {
				Token * token = memento->back();

				// Remove first...
				memento->pop_back();

				// Delete later...
				delete token;
			}

			// Delete later...
			delete memento;
		}

		while(!tokenQueue.empty()) {
			Token * token = tokenQueue.back();

			// Remove first...
			tokenQueue.pop_back();

			// Delete later...
			delete token;
		}
	}

	void Parser::parse() {
		std::cout << "> > > Parsing: " << filePath << " . . ." << std::endl;

			Token * token(0x00);

			for(/* void */;/* void */;/* void */) {
				token = read();

				if(token->type_id() == QUEX_UUID_EOF || token->type_id() == QUEX_UUID_FCK) {
					break;
				}

				std::cout << token->type_id_name();

				if(token->type_id() == QUEX_UUID_POINTIE) {
					std::cout << "(";
					// cln::fprint(std::cout,token->pointieValue);
					std::cout << ")";
				}

				std::cout << std::endl;

				if((std::rand() % 2) != 0) {
					markPosition();
				}
			}
	}

	void Parser::assemble() {
	}

	void Parser::write() {
	}

	Token * Parser::read() {
		deque<Token *> * memento = tokenMemento.top();
		Token* nextToken        = 0x00;

		if(tokenQueue.empty()) {
            Token*  token_p = 0x0;
			// Receive from lexer...
			lexer.receive(&token_p);
            nextToken = new Token(*token_p);
		} else {
			nextToken = tokenQueue.front();

			// Remove from queue...
			tokenQueue.pop_front();
		}

		// Push into current memento...
		memento->push_back(nextToken);

		return nextToken;
	}

	Token * Parser::peek() {
		return peek(0x01);
	}

	Token * Parser::peek(unsigned long int peekIndex) {
		Token * peekToken = 0x00;
		size_t queueSize  = tokenQueue.size();

		/*
			Convert peek-index to array-index...
		*/
		peekIndex--;

		if(peekIndex < queueSize) {
			peekToken = tokenQueue.at(peekIndex);
		} else {
			size_t needCount = (peekIndex + 1) - queueSize;

			for(int index = 0x00;index < needCount;index++) {
                Token*  token_p = 0x0;
                // Receive from lexer...
                lexer.receive(&token_p);
                Token* readToken = new Token(*token_p);

				// Push into look-ahead buffer...
				tokenQueue.push_back(readToken);
			}

			peekToken = tokenQueue.at(peekIndex);
		}

		return peekToken;
	}

	bool Parser::markPosition() {
		tokenMemento.push(new deque<Token *>());
		return true;
	}

	bool Parser::backtrack() {
		deque<Token *> * memento = tokenMemento.top();

		if(0x01 == tokenMemento.size()) {
			return false;
		}

		// Remove first...
		tokenMemento.pop();

		while(!memento->empty()) {
			Token * token = memento->back();

			memento->pop_back();
			tokenQueue.push_front(token);
		}

		// Delete later...
		delete memento;

		return true;
	}

	bool Parser::omitPosition() {
		deque<Token *> * memento = tokenMemento.top();

		if(0x01 == tokenMemento.size()) {
			return false;
		}

		// Remove first...
		tokenMemento.pop();

		while(!memento->empty()) {
			Token * token = memento->back();

			// Remove first...
			memento->pop_back();

			// Delete later...
			delete token;
		}

		// Delete later...
		delete memento;

		return true;
	}
}

int 
main(int argCount, char * argValues[]) 
{
	if(argCount < 0x02) {
		std::cout << "Usage:" << argValues[0x00] << " [options] <sources>" << std::endl;
		std::cout << std::endl;

		// Is this success?
		return EXIT_SUCCESS;
	}

	for(int argIndex = 0x01;argIndex < argCount;argIndex++) {
		Parser * parser = new Parser(argValues[argIndex],"UTF-8");

		parser->parse();
		parser->assemble();
		parser->write();

		delete parser;
	}

	// This is success!
	return EXIT_SUCCESS;
}
