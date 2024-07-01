require 'socket'

# Hook to debug from
b = Regexp.last_match

s = 'abcdefghijkmnopqrstuvwxy'
s.force_encoding "US-ASCII"

sock = TCPServer.new 'localhost', 1234

loop do
  puts "[/] Waiting for client"
  client = sock.accept

  loop do
    puts "[+] Reading input"
    line = client.gets
    if !line
      break
    end
    puts line.chomp
    re = Regexp.compile(line.chomp)
    match = s.match(re)
    if match
      client.write "match"
    else
      client.write "nomatch"
    end
  end
end
