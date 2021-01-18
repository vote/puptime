# Uptime Monitoring

By VoteAmerica

Citizens have an interest in ensuring that state web sites providing
voter tools are online and available, particularing during the period
leading up to an election or an election-related deadline.  Normal site
uptime monitoring tools are insufficient, however, for a few reasons:

- Simply checking whether the web server is responding is not
  sufficient, however, as backend systems may go down and result in a
  friendly "Currently Unavailable" message.  Puptime checks for
  specific keywords on the resulting pages.

- Many states employ generic security tools or appliances that have a
  tendency to block external tools that are regularly monitoring a web
  page.  Puptime makes it's page checks indistinguisable from humans
  by (1) using selenium to do a "normal" page load from a browser
  instance, and (2) directing those page loads through a
  dynamically-deployed and short-lived proxy server.

Puptime also archives the page source and a snapshot (PNG) of every
page load for future reference.

To see puptime deployed: https://uptime.voteamerica.com/
