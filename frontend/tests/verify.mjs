import {spawnSync} from 'node:child_process'
const npmCli=process.env.npm_execpath
if(!npmCli){console.error('Run this command through npm run verify.');process.exit(1)}
const checks=['build','lint','test','test:api','test:sources','test:reviews','test:posters','test:collaboration','test:approval','test:consent']
if(process.env.BRANDPROOF_RUN_BROWSER==='1')checks.push('test:browser')
for(const check of checks){
  const result=spawnSync(process.execPath,[npmCli,'run',check],{stdio:'inherit',env:process.env})
  if(result.status!==0){console.error(`Verification FAILED at ${check}. Remaining checks were not run.`);process.exit(result.status||1)}
}
console.log(`PASS ${checks.length} verification commands. ${process.env.BRANDPROOF_RUN_BROWSER==='1'?'Browser included.':'Browser not included; set BRANDPROOF_RUN_BROWSER=1 with the documented dedicated Chrome session.'}`)
