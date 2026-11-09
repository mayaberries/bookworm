Recorded catalogue responses, replayed through httpx.MockTransport so adapter
tests run offline. One folder per adapter system, one file per scenario,
named for what it shows. Record real responses with the `create-adapter`
skill's steps; trim them to what the test needs, and never commit personal
data (a patron's name on a hold, a session cookie).
