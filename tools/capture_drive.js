// Records a World Drive drive as video frames, using the dev-only capture hook
// (window.worldDriveCapture in TTVV-7/Neptune-digital-twin, src/drive-app/main.js).
//
// Needs World Drive's dev server running, e.g. from the Neptune-digital-twin checkout:
//   npx vite --config vite.drive.config.js --port 5199 --strictPort
// For the Moon, start it WITHOUT a Google key (env -u google_api ...); for Earth it reads the
// google_api key from the environment (billed per drive).
//
// Usage:
//   node tools/capture_drive.js <outDir> <place> [driveSeconds] [scale]
//   place: a spot id ("moon-tycho", "golden-gate") or "lat,lon[,world][,name]" e.g. "48.858,2.294,earth,Eiffel Tower"
//   scale: 2 = 1080x1920 frames (slow, ~6 s/frame in software), 1 = 540x960 (upscale later)
// Writes <outDir>/frames/%05d.jpg at 30 fps plus <outDir>/capture.json (credit, timings, place).

const { chromium } = require( 'playwright' );
const fs = require( 'fs' );
const path = require( 'path' );

const [ outDir, place, secondsArg = '18', scaleArg = '1' ] = process.argv.slice( 2 );
if ( ! outDir || ! place ) {

	console.error( 'usage: node tools/capture_drive.js <outDir> <place> [driveSeconds] [scale]' );
	process.exit( 2 );

}

const FPS = 30;
const DRIVE_SECONDS = Number( secondsArg );
const SCALE = Number( scaleArg );
const BASE = process.env.WORLD_DRIVE_URL || 'http://localhost:5199/';

function placeQuery( p ) {

	if ( ! p.includes( ',' ) ) return `?spot=${ encodeURIComponent( p ) }`;
	const [ lat, lon, world = 'earth', ...name ] = p.split( ',' );
	const q = new URLSearchParams( { at: `${ lat },${ lon }` } );
	if ( world === 'moon' ) q.set( 'world', 'moon' );
	if ( name.length ) q.set( 'name', name.join( ',' ) );
	return `?${ q }`;

}

// A drive with some life in it: straight off, then boost, weave, hop and drift.
// [ second, action ] — 'down'/'up' a key.
const SCRIPT = [
	[ 0.0, 'down', 'w' ],
	[ 1.5, 'down', 'Shift' ],
	[ 3.5, 'down', 'a' ], [ 4.3, 'up', 'a' ],
	[ 5.5, 'down', 'd' ], [ 6.4, 'up', 'd' ],
	[ 7.5, 'down', 'Space' ], [ 7.7, 'up', 'Space' ],
	[ 9.5, 'down', 'a' ], [ 10.2, 'up', 'a' ],
	[ 11.0, 'up', 'Shift' ],
	[ 11.5, 'down', 'Shift' ],
	[ 12.5, 'down', 'd' ], [ 12.8, 'down', 'Space' ], [ 13.0, 'up', 'Space' ], [ 13.6, 'up', 'd' ],
	[ 15.0, 'down', 'a' ], [ 15.6, 'up', 'a' ],
];

( async () => {

	const framesDir = path.join( outDir, 'frames' );
	fs.mkdirSync( framesDir, { recursive: true } );
	const browser = await chromium.launch( { args: [ '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist' ] } );
	const page = await browser.newPage( { viewport: { width: 540, height: 960 }, deviceScaleFactor: SCALE } );
	const t0 = Date.now();
	await page.goto( BASE + placeQuery( place ), { waitUntil: 'load', timeout: 90000 } );
	const drive = page.getByRole( 'button', { name: 'Drive here' } );
	await drive.waitFor( { timeout: 180000 } );
	// Let the globe finish flying to the pin and the ground load (in real time).
	await page.waitForTimeout( 20000 );

	await page.evaluate( () => window.worldDriveCapture.start() );
	let n = 0;
	const shot = async () => {

		const url = await page.evaluate( () => window.worldDriveCapture.step() );
		fs.writeFileSync( path.join( framesDir, `${ String( n ++ ).padStart( 5, '0' ) }.jpg` ), Buffer.from( url.split( ',' )[ 1 ], 'base64' ) );

	};

	// 1 s on the globe with the pin, then Drive here and the drop in.
	for ( let i = 0; i < FPS; i ++ ) await shot();
	const globeFrames = n;
	await drive.click( { timeout: 30000 } );
	// The drop: step until the HUD says we're driving (a speed readout), at most 8 s.
	let dropFrames = 0;
	for ( ; dropFrames < FPS * 8; dropFrames ++ ) {

		await shot();
		// Tiles and ground load in real time; give them a moment every few frames of the drop.
		if ( dropFrames % 10 === 0 ) await page.waitForTimeout( 1500 );
		const driving = await page.evaluate( () => /km\/h/.test( document.body.innerText ) );
		if ( driving && dropFrames > FPS ) break;

	}

	const driveStart = n;
	let next = 0;
	for ( let i = 0; i < DRIVE_SECONDS * FPS; i ++ ) {

		const t = i / FPS;
		while ( next < SCRIPT.length && SCRIPT[ next ][ 0 ] <= t ) {

			const [ , action, key ] = SCRIPT[ next ++ ];
			await ( action === 'down' ? page.keyboard.down( key ) : page.keyboard.up( key ) );

		}

		await shot();
		if ( i % 30 === 0 ) process.stdout.write( `\rframe ${ n } (${ ( ( Date.now() - t0 ) / 1000 ).toFixed( 0 ) } s)` );

	}

	const info = {
		place,
		fps: FPS,
		size: [ 540 * SCALE, 960 * SCALE ],
		frames: n,
		globeFrames,
		dropFrames: driveStart - globeFrames,
		driveStart,
		credit: await page.evaluate( () => window.worldDriveCapture.credit() ),
		placeName: await page.evaluate( () => document.querySelector( '#place-name, .place-name' )?.innerText ?? '' ),
		seconds: Math.round( ( Date.now() - t0 ) / 1000 ),
	};
	fs.writeFileSync( path.join( outDir, 'capture.json' ), JSON.stringify( info, null, '\t' ) );
	console.log( '\n' + JSON.stringify( info ) );
	await browser.close();

} )().catch( err => {

	console.error( 'FAIL', err.message );
	process.exit( 1 );

} );
