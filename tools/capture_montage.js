// Records a World Drive stunt montage: several places in one page load (one Google Maps session),
// a few seconds of full-boost driving at each, with the game's own stunt call-outs on screen.
// Uses World Drive's dev-only capture hook (window.worldDriveCapture) to step the game one video
// frame at a time, and grabs the whole page so the call-outs ("Wall bounce", "WHAM!", "Big air")
// and the map credit are in the frames. The speed panel, key hints and top bar are hidden.
//
// Needs World Drive's dev server (Neptune-digital-twin checkout, branch with the hook):
//   npx vite --config vite.drive.config.js --port 5199 --strictPort            (Earth: uses google_api)
//   env -u google_api npx vite --config vite.drive.config.js --port 5199 ...   (Moon only)
//
// Usage: node tools/capture_montage.js <outDir> <spot>[,<spot>...] [secondsPerPlace] [seed]
//   spots: World Drive spot ids, e.g. furka,sydney,lions-gate,arc  or  moon-huygens,moon-tycho
// Writes <outDir>/clip-<n>/%05d.jpg (30 fps, 540x960) and <outDir>/montage.json.

const { chromium } = require( 'playwright' );
const fs = require( 'fs' );
const path = require( 'path' );

const [ outDir, spotsArg, secondsArg = '5', seedArg = '1' ] = process.argv.slice( 2 );
if ( ! outDir || ! spotsArg ) {

	console.error( 'usage: node tools/capture_montage.js <outDir> <spot,spot,...> [secondsPerPlace] [seed]' );
	process.exit( 2 );

}

const FPS = 30;
const SPOTS = spotsArg.split( ',' );
const SECONDS = Number( secondsArg );
const BASE = process.env.WORLD_DRIVE_URL || 'http://localhost:5199/';
// Spot id → the name on its globe-panel button, from World Drive's own place lists.
const SRC = process.env.WORLD_DRIVE_SRC || '/home/user/neptune-digital-twin';
const NAMES = {};
for ( const file of [ 'src/drive-app/places.js', 'src/drive-app/moon-places.js' ] ) {

	const text = fs.existsSync( path.join( SRC, file ) ) ? fs.readFileSync( path.join( SRC, file ), 'utf8' ) : '';
	for ( const m of text.matchAll( /id: '([a-z0-9-]+)', name: '((?:[^'\\]|\\.)+)'/g ) ) NAMES[ m[ 1 ] ] = m[ 2 ].replace( /\\'/g, '\'' );
	for ( const m of text.matchAll( /moon\( '([a-z0-9-]+)', '((?:[^'\\]|\\.)+)'/g ) ) NAMES[ `moon-${ m[ 1 ] }` ] = m[ 2 ].replace( /\\'/g, '\'' );

}

let seed = Number( seedArg ) || 1;
const rand = () => ( seed = ( seed * 16807 ) % 2147483647 ) / 2147483647;

// Hide the driving dashboard; keep the stunt call-outs (.dhud-flash/.dhud-tricks/.dhud-pops) and credit.
const CSS = `.dhud-cluster, .dhud-keys, .dhud-touch, #drive-ui .topbar, .live-tags, #toast { visibility: hidden !important; }`;

// A wild line: full boost, hard steering into whatever is beside the road, hops. Returns
// [ frame, 'down'|'up', key ] events for one clip.
function stuntScript( frames ) {

	const ev = [ [ 0, 'down', 'w' ], [ 0, 'down', 'Shift' ] ];
	let f = Math.round( FPS * ( 0.3 + rand() * 0.4 ) );
	while ( f < frames - 10 ) {

		const r = rand();
		if ( r < 0.6 ) {

			const key = rand() < 0.5 ? 'a' : 'd';
			const len = Math.round( FPS * ( 0.3 + rand() * 0.6 ) );
			ev.push( [ f, 'down', key ], [ f + len, 'up', key ] );
			f += len + Math.round( FPS * ( 0.2 + rand() * 0.4 ) );

		} else {

			ev.push( [ f, 'down', 'Space' ], [ f + 5, 'up', 'Space' ] );
			f += Math.round( FPS * ( 0.5 + rand() * 0.5 ) );

		}

	}

	return ev.sort( ( a, b ) => a[ 0 ] - b[ 0 ] );

}

async function releaseAll( page ) {

	for ( const k of [ 'w', 'a', 'd', 'Shift', 'Space' ] ) await page.keyboard.up( k );

}

( async () => {

	fs.mkdirSync( outDir, { recursive: true } );
	const browser = await chromium.launch( { args: [ '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist' ] } );
	const page = await browser.newPage( { viewport: { width: 540, height: 960 } } );
	const t0 = Date.now();
	await page.goto( `${ BASE }?spot=${ encodeURIComponent( SPOTS[ 0 ] ) }`, { waitUntil: 'load', timeout: 90000 } );
	await page.addStyleTag( { content: CSS } );
	const clips = [];

	for ( let i = 0; i < SPOTS.length; i ++ ) {

		const spot = SPOTS[ i ];
		if ( i > 0 ) {

			// Back to the globe, then the spot's button on the panel (same page, same Maps session).
			await releaseAll( page );
			await page.evaluate( () => window.worldDriveCapture.stop() );
			await page.keyboard.press( 'm' );
			await page.waitForTimeout( 6000 );
			const name = NAMES[ spot ] ?? null;
			const button = name ? page.getByRole( 'button', { name, exact: true } ) : null;
			if ( button && await button.count() ) await button.first().click();
			else await page.goto( `${ BASE }?spot=${ encodeURIComponent( spot ) }`, { waitUntil: 'load', timeout: 90000 } ).then( () => page.addStyleTag( { content: CSS } ) );

		}

		const drive = page.getByRole( 'button', { name: 'Drive here' } );
		await drive.waitFor( { timeout: 180000 } );
		await page.waitForTimeout( 12000 );
		await drive.click();
		// The drop in and the ground loading, in real time (not recorded).
		await page.waitForFunction( () => /km\/h/.test( document.body.innerText ), null, { timeout: 120000 } ).catch( () => {} );
		await page.waitForTimeout( 20000 );
		const place = await page.evaluate( () => document.querySelector( '#drive-ui .place' )?.textContent?.trim() ?? '' );

		const dir = path.join( outDir, `clip-${ i }` );
		fs.mkdirSync( dir, { recursive: true } );
		const frames = Math.round( SECONDS * FPS );
		const events = stuntScript( frames );
		let next = 0;
		await page.evaluate( () => window.worldDriveCapture.start() );
		for ( let f = 0; f < frames; f ++ ) {

			while ( next < events.length && events[ next ][ 0 ] <= f ) {

				const [ , action, key ] = events[ next ++ ];
				await ( action === 'down' ? page.keyboard.down( key ) : page.keyboard.up( key ) );

			}

			await page.evaluate( () => { window.worldDriveCapture.step(); } );
			await page.screenshot( { path: path.join( dir, `${ String( f ).padStart( 5, '0' ) }.jpg` ), quality: 88, timeout: 60000 } );

		}

		const credit = await page.evaluate( () => window.worldDriveCapture.credit() );
		clips.push( { spot, place, frames, credit } );
		console.log( `${ spot } (${ place }): ${ frames } frames, ${ Math.round( ( Date.now() - t0 ) / 1000 ) } s` );

	}

	fs.writeFileSync( path.join( outDir, 'montage.json' ), JSON.stringify( { fps: FPS, size: [ 540, 960 ], clips }, null, '\t' ) );
	await browser.close();

} )().catch( err => {

	console.error( 'FAIL', err.message );
	process.exit( 1 );

} );
