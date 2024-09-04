package logger

import (
	"context"
	"fmt"
	"strings"
)

var InDebugRange = false

var XiaochenLogger *Logger

func init() {
	XiaochenLogger, _ = RootLogger("", true)
}

func Print(f string, args ...interface{}) {
	if !InDebugRange {
		return
	}

	XiaochenLogger.PrintfCtxDepth(context.Background(), 2 /* depth */, f, args...)
}

func RawPrint(f string, args ...interface{}) {
	if !InDebugRange {
		return
	}

	// add a newline to the end of the message, if it doesn't already have one
	if !strings.HasSuffix(f, "\n") {
		f += "\n"
	}

	fmt.Printf(f, args...)
}
