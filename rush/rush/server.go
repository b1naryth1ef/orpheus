package rush

import (
	"./json"
	"fmt"
	"github.com/gorilla/websocket"
	"gopkg.in/redis.v2"
	"log"
	"net/http"
	"strconv"
	"strings"
)

var upgrader = &websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin:     func(r *http.Request) bool { return true },
}

var red *redis.Client

type Session struct {
}

type Connection struct {
	id     int
	uid    float64
	Active bool
	Conn   *websocket.Conn
}

type Server struct {
	Addr  string
	Conns map[int]*Connection
	PS    *redis.PubSub

	Active bool
	idinc  int
}

func NewServer(addr string) *Server {
	return &Server{
		Addr:   addr,
		Conns:  make(map[int]*Connection),
		Active: true,
	}
}

func (c *Connection) readFromSocketLoop(s *Server) {
	for {
		_, data, err := c.Conn.ReadMessage()
		if err != nil {
			break
		}

		msg := string(data)
		if strings.HasPrefix(msg, "auth") {
			log.Printf("Got auth request: `%v`", msg)
			values := strings.Split(msg, " ")
			if len(values) <= 2 && len(values[1]) == 36 {
				result := red.Get("session:" + values[1])
				if result.Err() != nil {
					log.Printf("ERROR: failed to get session from redis: %v", result.Err())
					continue
				}

				obj := json.LoadJson([]byte(result.Val()))
				if obj.Value("u").(float64) > 0 {
					log.Printf("Connection %v has authed (user: %v)", c.id, obj.Value("u"))
					c.uid = obj.Value("u").(float64)

					// Subscribe to the channel
					chan_n := fmt.Sprintf("ws:user:%v", obj.Value("u"))
					log.Printf("`%v`", chan_n)
					err := s.PS.Subscribe(chan_n)
					if err != nil {
						log.Fatal("Failed to subscribe to user websocket channel (%v): %v", obj.Value("u"), err)
						return
					}
				}
			}
		}
	}
	c.Conn.Close()
}

func (s *Server) sendToAll(data []byte) {
	for _, vc := range s.Conns {
		vc.Conn.WriteMessage(websocket.TextMessage, data)
	}
}

func (s *Server) serverLoop() {
	s.PS = red.PubSub()
	defer s.PS.Close()

	err := s.PS.Subscribe("ws:global")
	if err != nil {
		log.Fatal("Failed to subscribe to global websocket channel: %v", err)
		return
	}

	for s.Active {
		msg, err := s.PS.Receive()
		if err != nil {
			log.Fatal("PS Recieve error: %v", err)
			continue
		}

		switch v := msg.(type) {
		case *redis.Message:
			msgR := msg.(*redis.Message)
			splitC := strings.Split(msgR.Channel, ":")
			if len(splitC) < 2 {
				log.Printf("Invalid incoming channel: %v", msgR.Channel)
				continue
			}

			if splitC[1] == "global" {
				s.sendToAll([]byte(msgR.Payload))
				continue
			}

			if splitC[1] == "user" && len(splitC) >= 3 {
				uidV, _ := strconv.Atoi(splitC[2])

				// lol O(n) xD
				for _, vc := range s.Conns {
					if vc.uid == float64(uidV) {
						vc.Conn.WriteMessage(websocket.TextMessage, []byte(msgR.Payload))
					}
				}
				continue
			}

			_ = v
		}
	}
}

func (s *Server) addSocket(c *Connection) {
	for {
		if _, exists := s.Conns[s.idinc]; !exists {
			break
		}
		s.idinc++
	}

	s.Conns[s.idinc] = c
	c.id = s.idinc
	log.Printf("Added socket w/ ID %v, now have %v sockets...", s.idinc, len(s.Conns))
}

func (s *Server) statsHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Connections: %v", len(s.Conns))
}

func (s *Server) webSocketHandler(w http.ResponseWriter, r *http.Request) {
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Error upgrading socket: %v", err)
		return
	}

	log.Printf("Attempting new websocket connection")
	c := &Connection{Conn: ws, Active: true, uid: -1}
	s.addSocket(c)

	c.readFromSocketLoop(s)

	c.Active = false
	delete(s.Conns, c.id)

	log.Printf("Closing socket w/ ID %v, now have %v sockets...", c.id, len(s.Conns))
}

func (s *Server) RunServer(redisHost string) {
	red = redis.NewClient(&redis.Options{
		Network: "tcp",
		Addr:    redisHost,
	})

	go s.serverLoop()
	http.HandleFunc("/", s.webSocketHandler)
	http.HandleFunc("/stats", s.statsHandler)
	log.Printf("Starting service...")
	http.ListenAndServe(s.Addr, nil)
}
