// TOKENIZER
// www.ctrl-pomme-reset.fr (c) 2014
//
// Command line tool to "tokenize" Applesoft code (text file) to a binary file.
// Based on CiderPress Code by Andy McFadden (c) FaddenSoft:
//  use (and abuse) of code from "Import Basic Function" from CiderPress.
//
// Tokenizer and its source code are released under BSD License.
//
//
// usage: 
// Tokenizer.exe <applesoft source file> [tokenized output file] [-q]
// option : -q (quiet mode)
//
//
// version history:
// 0.5x : first version released 
//
//
//
#define VERSION "0.55"

// Commented this out -gg
// #include <windows.h>



// added this since C was chokcing on bool --gg
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>

// Added this define to get around Windows -> Linux issue
#define strnicmp strncasecmp
#define _strnicmp strncasecmp


#define false	0
#define true	1

#define NUMTOKENS 107

// fonctions
bool ImportBAS(const char*, const char*);
bool ConvertTextToBAS(const char*, long);
bool ProcessBASLine(const char*, int, int*);
bool FixBASLinePointers(char*, long , unsigned short, int*);
const char* FindEOL(const char*, long);
bool GetNextNWC(const char**, int*, char*);
int Lookup(const char*, int, int*);
//

static const char* kFailed = "failed!\r\n\r\n";
static const char* kSuccess = "success!\r\n\r\n";
static const char* FileOutDefault = "applesoft.bin";


static const char *Errormsg[] = {"found nothing except line number.",
								 "line number has too many digits.",
								 "line did not start with a line number."};

static const char gApplesoftTokens[NUMTOKENS*8] = {
    "END\0FOR\0NEXT\0DATA\0INPUT\0DEL\0DIM\0READ\0"
    "GR\0TEXT\0PR#\0IN#\0CALL\0PLOT\0HLIN\0VLIN\0"
    "HGR2\0HGR\0HCOLOR=\0HPLOT\0DRAW\0XDRAW\0HTAB\0HOME\0"
	"ROT=\0SCALE=\0SHLOAD\0TRACE\0NOTRACE\0NORMAL\0INVERSE\0FLASH\0"
	"COLOR=\0POP\0VTAB\0HIMEM:\0LOMEM:\0ONERR\0RESUME\0RECALL\0"
	"STORE\0SPEED=\0LET\0GOTO\0RUN\0IF\0RESTORE\0&\0"
	"GOSUB\0RETURN\0REM\0STOP\0ON\0WAIT\0LOAD\0SAVE\0"
	"DEF\0POKE\0PRINT\0CONT\0LIST\0CLEAR\0GET\0NEW\0"
	"TAB(\0TO\0FN\0SPC(\0THEN\0AT\0NOT\0STEP\0"
	"+\0-\0*\0/\0^\0AND\0OR\0>\0"
	"=\0<\0SGN\0INT\0ABS\0USR\0FRE\0SCRN(\0"
	"PDL\0POS\0SQR\0RND\0LOG\0EXP\0COS\0SIN\0"
	"TAN\0ATN\0PEEK\0LEN\0STR$\0VAL\0ASC\0CHR$\0"
	"LEFT$\0RIGHT$\0MID$\0"
};

char* Buffer = 0;
int idx = 0; // Changed this from index, which apparently is a standard function
bool quiet = 0;

int fTokenLen[NUMTOKENS];
const char* fTokenPtr[NUMTOKENS];

int main(int argc, char *argv[])

{
	const char* tokenList;
	int count;
	const char* FileOut;
	char* FileIn;

	FileOut =0;
	FileIn =0;
	

	// récupération param 1, param 2 et option(s)
	for (count = 1; count < argc; count++){
	
	    // Replaced _strcmpi globally with strcasecmp
		if (strcasecmp(argv[count],"-q") == 0 && quiet == 0){
		quiet = 1;
		continue;
		}

		if (!FileIn){
		FileIn = argv[count];
		continue;
		}
		if (!FileOut){
		FileOut = argv[count];
		continue;
		}
	}

	
	if (!quiet || !FileIn) {
	printf("Tokenizer version "VERSION" (c) www.ctrl-pomme-reset.fr 2014.\r\n");
	printf("Based on CiderPress Source Code by Andy McFadden (c) FaddenSoft 2009.\r\n\r\n");
	}
	// si pas d'argument afficher message d'aide ! + fin
	if (!FileIn){
	printf("usage  : tokenize-asoft <applesoft source file> [tokenized output file] [-q]\r\n");
	printf("option : ");
	printf("-q quiet mode\r\n"); 
	//getchar();  
	return 1;
	}

	if (!FileOut){	// si fichier de sortie non précisé, nom par défaut
	FileOut = FileOutDefault;
	}



// init -> chargement des Tokens dans un tableau

	tokenList = gApplesoftTokens; // début de la chaine des Tokens

	for (count = 0; count < NUMTOKENS; count++) {
		fTokenPtr[count] = tokenList;
		fTokenLen[count] = (int)strlen(fTokenPtr[count]);
		tokenList += fTokenLen[count];
		tokenList++; // on shunte le 0 de fin de chaque token!
	}

	if (!ImportBAS(FileIn, FileOut)) {
		//getchar();	// debug
		return 0;		// tout est OK
	}
	else	{			// si erreur...
	getchar();			// attente de l'appui sur RETURN
	return 1;			// sortie à 1
	}

}

bool ImportBAS(const char* FileName, const char* FileOut)
{
	char* buf = NULL;
	FILE* fp = NULL;
	FILE* fOut = NULL;
	bool result = 1;
	int fileLen, count, ret;

	if (!quiet) {
		printf("Converting from '%s' : ", FileName);
	}
	// switched from fopen_s to fopen (see http://stackoverflow.com/questions/2575116/fopen-fopen-s-and-writing-to-files)
	/*
	ret = fopen_s(&fp,FileName, "rb"); 
	if (ret != 0) {
		if (!quiet) {
		printf("%s-> Unable to open file.", kFailed);
		}
		goto bail;
	}
	*/
	ret = (fp = fopen(FileName, "rb")); 
	if (ret == NULL) {
		if (!quiet) {
		printf("%s-> Unable to open file.", kFailed);
		}
		goto bail;
	}
	/* determi#define strnicmp strncasecmpne file length, and verify that it looks okay */
	fseek(fp, 0, SEEK_END);
	fileLen = ftell(fp);
	rewind(fp);
	if (ferror(fp) || fileLen < 0) {
		if (!quiet) {
		printf("%s-> Unable to determine file length.", kFailed);
		}
		goto bail;
	}
	if (fileLen == 0) {
		if (!quiet) {
		printf("%s-> File is empty.", kFailed);
		}
		goto bail;
	}
	if (fileLen >= 128*1024) {
		if (!quiet) {
		printf("%s-> File is too large to be Applesoft.", kFailed);
		}
		goto bail;
	}

	buf = malloc(fileLen);
	if (buf == NULL) {
		if (!quiet) {
		printf("%s-> Unable to allocate memory.", kFailed);
		}
		goto bail;
	}

	/* read the entire thing into memory */
	count = (int)fread(buf, 1, fileLen, fp);
	if (count != fileLen) {
		if (!quiet) {
		printf("%s-> Could only read %ld of %ld bytes.", kFailed,
			count, fileLen);
		}
		goto bail;
	}

	Buffer = malloc(0xC000);

	/* process it */
	if (!ConvertTextToBAS(buf, fileLen))
		goto bail;
	if (!quiet) {
		printf("\r\nSaving to %s : ", FileOut);
	}

    // fopen_s -> fopen
    /*
	ret = fopen_s(&fOut,FileOut,"wb"); //
	if (ret != 0) {
		if (!quiet) {
		printf("%s-> Unable to create file.", kFailed);
		}
		goto bail;
	} */
	ret = (fOut = fopen(FileOut,"wb")); //
	if (ret == NULL) {
		if (!quiet) {
		printf("%s-> Unable to create file.", kFailed);
		}
		goto bail;
	}

	count = (int)fwrite(Buffer,1,idx,fOut);
	if (count != idx) {
		if (!quiet) {
		printf("%s-> Unable to write file.", kFailed);
		}
		goto bail;
	}

	if (!quiet) {
	printf("%s",kSuccess);
	}
	result = 0; // success

bail:
	if (fp != NULL)
		fclose(fp);
	if (fOut != NULL)
		fclose(fOut);
	if (buf !=NULL)
		free(buf);
	if (Buffer !=NULL)
		free(Buffer);

	return result;
}

bool ConvertTextToBAS(const char* buf, long fileLen)
{
	const char* lineStart;
	const char* lineEnd;
	int msg;
	int textRemaining;
	int lineNum;
	int val;
	

	lineEnd = buf;
	textRemaining = fileLen;
	lineNum = 0;
	
	val = 0;
	idx = 0;

	while (textRemaining > 0) {
		lineNum++;
		lineStart = lineEnd;
		lineEnd = FindEOL(lineStart, textRemaining);

		if (!ProcessBASLine(lineStart, (int)(lineEnd - lineStart), &msg))
		{
			if (!quiet) {

				printf("%s-> Problem with line %d : %s", kFailed, lineNum, Errormsg[msg]);
			}
			return 0;
		}

		textRemaining -= (int)(lineEnd - lineStart);
	}

	/* output EOF marker */
	Buffer[idx]=(0x00);
	idx++;
	Buffer[idx]=(0x00);
	idx++; // ? nécessaire ?!

	if (idx >= 0xc000) {
		if (!quiet) {
		printf("%s-> Output is too large to be valid.", kFailed);
		}
		return 0;
	}

	/* go back and fix up the "next line" pointers, assuming a $0801 start */
	if (!FixBASLinePointers(Buffer, idx, 0x0801,&val)) {
		if (!quiet) {
			if (val){
				printf("%s-> Failed while fixing line pointers : unexpected value 0x%04x found.", kFailed,val);			
			}
			else {
				printf("%s-> Failed while fixing line pointers : ran off the end?",kFailed);
			}
		}
		return 0;
	}

	if (!quiet) {
	printf("%sProcessed %d lines.", kSuccess, lineNum);
	printf("\r\nTokenized file is %d bytes long.", idx);
	printf("\r\n");
	}

	return 1;

}

bool ProcessBASLine(const char* buf, int len, int *msg)
{
	const int kMaxTokenLen = 7;		// longest token; must also hold linenum
	const int kTokenAT = 0xc5 - 128;
	const int kTokenATN = 0xe1 - 128;
	char tokenBuf[8];
	bool gotOne = false;
	bool haveLineNum = false;
	char ch;
	int tokenLen;
	int lineNum;
	int foundToken;

	int j;

	if (!len)
		return false;

	/*
	 * Remove the CR, LF, or CRLF from the end of the line.
	 */
	if (len > 1 && buf[len-2] == '\r' && buf[len-1] == '\n') {
		//WMSG0("removed CRLF\n");
		len -= 2;
	} else if (buf[len-1] == '\r') {
		//WMSG0("removed CR\n");
		len--;
	} else if (buf[len-1] == '\n') {
		//WMSG0("removed LF\n");
		len--;
	} else {
		//WMSG0("no EOL marker found\n");
	}

	if (!len)
		return true;		// blank lines are okay

	/*
	 * Extract the line number.
	 */
	tokenLen = 0;
	while (len > 0) {
		if (!GetNextNWC(&buf, &len, &ch)) {
			if (!gotOne)
				return true;		// blank lines with whitespace are okay
			else {
				// end of line reached while scanning line number is bad
				*msg = 0; 
				return false;
			}
		}
		gotOne = true;

		if (!isdigit(ch))
			break;
		if (tokenLen == 5) {	// theoretical max is "65535"
			*msg = 1;
			return false;
		}
		tokenBuf[tokenLen++] = ch;
	}

	if (!tokenLen) {
		*msg = 2;
		return false;
	}
	tokenBuf[tokenLen] = '\0';
	lineNum = atoi(tokenBuf);
	//printf("\r\nFOUND line %d\n", lineNum);

	Buffer[idx]= ((char) 0xcc);		// placeholder
	idx++;

	Buffer[idx]= ((char) 0xcc);
	idx++;
	Buffer[idx]= (lineNum & 0xff);
	idx++;
	Buffer[idx]= ((lineNum >> 8) & 0xff);
	idx++;

	/*
	 * Start scanning tokens.
	 *
	 * We need to find the longest matching token (i.e. prefer "ONERR" over
	 * "ON").  Grab a bunch of characters, ignoring whitespace, and scan
	 * for a match.
	 */
	buf--;			// back up
	len++;
	foundToken = -1;

	while (len > 0) {
		const char* dummy = buf;
		int remaining = len;

		/* load up the buffer */
		for (tokenLen = 0; tokenLen < kMaxTokenLen; tokenLen++) {
			if (!GetNextNWC(&dummy, &remaining, &ch))
				break;
			if (ch == '"')
				break;
			tokenBuf[tokenLen] = ch;
		}

		if (tokenLen == 0) {
			if (ch == '"') {
				/*
				 * Note it's possible for strings to be unterminated.  This
				 * will go unnoticed by Applesoft if it's at the end of a
				 * line.
				 */
				GetNextNWC(&buf, &len, &ch);
				Buffer[idx]=ch;
				idx++;
				while (len--) {
					ch = *buf++;
					Buffer[idx]=ch;
					idx++;
					if (ch == '"')
						break;
				}
			} else {
				/* end of line reached */
				break;
			}
		} else {
			int token, foundLen;

			token = Lookup(tokenBuf, tokenLen, &foundLen);
			if (token >= 0) {
				/* match! */
				if (token == kTokenAT || token == kTokenATN) {
					/* have to go back and re-scan original */
					const char* tp = buf +1;
					while (toupper(*tp++) != 'T')
						;
					if (toupper(*tp) == 'N') {
						/* keep this token */
						//assert(token == kTokenATN);
					} else if (toupper(*tp) == 'O') {
						/* eat and emit the 'A' so we get the "TO" instead */
						goto output_single;
					} else {
						if (token == kTokenATN) {
							/* reduce to "AT" */
							token = kTokenAT;
							foundLen--;
						}
					}
				}
				Buffer[idx]= (token + 128);
				idx++;

				/* consume token chars, including whitespace */
				for (j = 0; j < foundLen; j++)
					GetNextNWC(&buf, &len, &ch);

				//WMSG2("TOKEN '%s' (%d)\n",
				//	fBASLookup.GetToken(token), tokenLen);

				/* special handling for REM or DATA */
				if (token == 0xb2 - 128) {
					/* for a REM statement, copy verbatim to end of line */
					if (*buf == ' ') {
						/* eat one leading space, if present */
						buf++;
						len--;
					}
					while (len--) {
						ch = *buf++;
						Buffer[idx]=ch;
						idx++;
					}
				} else if (token == 0x83 - 128) {
					bool inQuote = false;

					/* for a DATA statement, copy until ':' */
					if (*buf == ' ') {
						/* eat one leading space */
						buf++;
						len--;
					}
					while (len--) {
						ch = *buf++;
						if (ch == '"')	// ignore ':' in quoted strings
							inQuote = !inQuote;

						if (!inQuote && ch == ':') {
							len++;
							buf--;
							break;
						}
						Buffer[idx]=ch;
						idx++;
					}
				}
			} else {
				/*
				 * Not a quote, and no token begins with this character.
				 * Output it and advance.
				 */
output_single:
				GetNextNWC(&buf, &len, &ch);
				Buffer[idx]=(toupper(ch));
				idx++;
			}
		}
	}

	Buffer[idx]=('\0');
	idx++;

	return true;
}

/*
 * Fix up the line pointers.  We left dummy nonzero values in them initially.
 */
bool FixBASLinePointers(char* buf, long len, unsigned short addr, int *retval)
{
	unsigned short val;
	char* start;

	while (len >= 4) {
		start = buf;
		val = (*buf) & 0xff | (*(buf+1)) << 8;

		if (val == 0)
			break;
		if (val != 0xcccc) {
			*retval = val;
			return false;
		}

		buf += 4;
		len -= 4;

		/*
		 * Find the next end-of-line marker.
		 */
		while (*buf != '\0' && len > 0) {
			buf++;
			len--;
		}
		if (!len) {
			*retval = 0;
			return false;
		}
		buf++;
		len--;

		/*
		 * Set the value.
		 */
		val = (unsigned short) (buf - start);
		//ASSERT((int) val == buf - start);
		addr += val;

		*start = addr & 0xff;
		*(start+1) = (addr >> 8) & 0xff;
	}

	return true;
}

/*
 * Look for the end of line.
 *
 * Returns a pointer to the first byte *past* the EOL marker, which will point
 * at unallocated space for last line in the buffer.
 */
const char* FindEOL(const char* buf, long max)
{
	if (max == 0)
		return 0;

	while (max) {
		if (*buf == '\r' || *buf == '\n') {
			if (*buf == '\r' && max > 0 && *(buf+1) == '\n')
				return buf+2;
			return buf+1;
		}

		buf++;
		max--;
	}

	/*
	 * Looks like the last line didn't have an EOL.  That's okay.
	 */
	return buf;
}

/*
 * Find the next non-whitespace character.
 *
 * Updates the buffer pointer and length.
 *
 * Returns "false" if we run off the end without finding another non-ws char.
 */
bool GetNextNWC(const char** pBuf, int* pLen, char* pCh)
{
	static const char* kWhitespace = " \t\r\n";

	while (*pLen > 0) {
		const char* ptr;
		char ch;

		ch = **pBuf;
		ptr = strchr(kWhitespace, ch);
		(*pBuf)++;
		(*pLen)--;

		if (ptr == 0) {
			*pCh = ch;
			return true;
		}
	}

	return false;
}

int Lookup(const char* str, int len, int* pFoundLen)
{
	int longestidx, longestLen;
	int i;

	longestidx = longestLen = -1;
	for (i = 0; i < NUMTOKENS; i++) {
		if (fTokenLen[i] <= len && fTokenLen[i] > longestLen &&
			_strnicmp(str, fTokenPtr[i], fTokenLen[i]) == 0)
		{
			longestidx = i;
			longestLen = fTokenLen[i];
		}
	}

	*pFoundLen = longestLen;
	return longestidx;
}

