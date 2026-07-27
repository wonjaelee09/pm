import fs from 'node:fs';
const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const required = ['Career AI Transition Tracker','Weekly scoreboard','Backlog','In progress','Done','Check-in input','Snowflake','LLM eval'];
const missing = required.filter(x => !html.includes(x));
if (missing.length) {
  console.error('Missing markers:', missing.join(', '));
  process.exit(1);
}
console.log('validation ok');
