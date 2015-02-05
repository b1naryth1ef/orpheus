package main

import (
	"./rush"
	"flag"
)

var (
	addr  = flag.String("addr", "0.0.0.0:7080", "Service Address")
	redis = flag.String("redis", "localhost:6379", "Redis Host")
)

func main() {
	flag.Parse()
	s := rush.NewServer(*addr)
	s.RunServer(*redis)
}
