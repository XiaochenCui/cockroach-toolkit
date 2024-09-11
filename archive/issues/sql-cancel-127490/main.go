package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
)

const url = "postgresql://root@10.0.0.90:25258/defaultdb?sslmode=disable"

func init() {
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)
}

func main() {
	go runningSession()

	time.Sleep(3 * time.Second)

	conn, err := pgx.Connect(context.Background(), url)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v\n", err)
	}
	defer conn.Close(context.Background())

	targetSession := getTargetSession(conn)
	log.Printf("targetSession: %s\n", targetSession)

	time.Sleep(3000 * time.Second)

	rows, err := conn.Query(context.Background(), "CANCEL SESSION $1;", targetSession)
	if err != nil {
		log.Fatalf("Query failed: %v\n", err)
		os.Exit(1)
	}
	for rows.Next() {
		row, err := rows.Values()
		if err != nil {
			log.Fatalf("Scan failed: %v\n", err)
			os.Exit(1)
		}
		log.Printf("%v\n", row[0])
	}

	// cancel the target session
	_, err = conn.Exec(context.Background(), "CANCEL SESSION $1;", targetSession)
	if err != nil {
		log.Fatalf("Query failed: %v\n", err)
		os.Exit(1)
	}

	time.Sleep(3 * time.Second)
}

// a session that print a heartbeat every second
func runningSession() {
	conn, err := pgx.Connect(context.Background(), url)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close(context.Background())

	i := 0
	for {
		// sql := `
		// SELECT '>>> HEARTBEAT <<<';
		// `

		sql := `
		SELECT COUNT(*)
		FROM generate_series(1, 100000000) AS gs, generate_series(1, 100) AS gs2;
		`

		rows, err := conn.Query(context.Background(), sql)
		if err != nil {
			log.Fatalf("Query failed: %v\n", err)
			os.Exit(1)
		}

		for rows.Next() {
			row, err := rows.Values()
			if err != nil {
				log.Fatalf("Scan failed: %v\n", err)
				os.Exit(1)
			}

			if i < 7 {
				log.Printf("%s\n", row[0])
			}
		}

		time.Sleep(1 * time.Second)

		i++
	}
}

func getTargetSession(conn *pgx.Conn) (sessionID string) {
	rows, err := conn.Query(context.Background(), `
		WITH sessions AS (
			SHOW CLUSTER SESSIONS
		)
		SELECT session_id, user_name, session_start, last_active_query, application_name
		FROM sessions;
		`)
	if err != nil {
		log.Fatalf("Query failed: %v\n", err)
		os.Exit(1)
	}

	sessionIDList := make([]string, 0)

	for rows.Next() {
		row, err := rows.Values()
		if err != nil {
			log.Fatalf("Scan failed: %v\n", err)
			os.Exit(1)
		}
		log.Printf("session_id: %s, user_name: %s, session_start: %s, last_active_query: %s\n",
			row[0], row[1], row[2], row[3])

		id := row[0].(string)
		if strings.Contains(row[3].(string), ">>> HEARTBEAT <<<") {
			sessionID = id
		}

		applicationName := row[4].(string)
		if !strings.Contains(applicationName, "cockroach") {
			sessionIDList = append(sessionIDList, id)
		}
	}

	for _, id := range sessionIDList {
		fmt.Printf("CANCEL SESSION '%s';\n", id)
	}

	return sessionID
}
