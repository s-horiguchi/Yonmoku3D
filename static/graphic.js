var camera, scene, renderer,controls,container,stats;
var spheres,cylinders;
var mouse = { x: 0, y: 0 }, INTERSECTED,raycaster;

function init() {
    var x,y,z;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 2000 );
    scene.add(camera);
    controls = new THREE.TrackballControls( camera );
    renderer = new THREE.WebGLRenderer({antialias:true, alpha: true });
    //renderer = new THREE.CSS3DRenderer();
    renderer.setClearColor( 0xffffff, 1);
    renderer.setSize( window.innerWidth, window.innerHeight );
    container = document.getElementById( 'ThreeJS' );
    container.appendChild( renderer.domElement );

    camera.position.set(0,5,5);
    camera.lookAt(scene.position);
    
    
    spheres = new Array;
    cylinders = new Array;
    
    for(x = 0; x < 4; x++) {
	for (y = 0; y < 4; y++) {
	    for (z=0; z < 4; z++) {
		// Sphere parameters: radius, segments along width, segments along height
		var sphereGeometry = new THREE.SphereGeometry( 0.4, 32, 16 ); 
		var sphereMaterial = new THREE.MeshLambertMaterial( {color: 0x8888ff} ); 
		var sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
		sphere.position.set(x-2,z*0.8,y-2);
		sphere.name = "sphere"+x+","+y+","+z;
		sphere.visible = false;
		scene.add(sphere);
		spheres.push( sphere );
		
	    }
	}
    }
    for(x=0; x < 4; x++) {
	for(y=0; y < 4; y++) {
	    // cylinder
	    // radiusAtTop, radiusAtBottom, height, segmentsAroundRadius, segmentsAlongHeight
	    var geomet = new THREE.CylinderGeometry( 0.1, 0.1, 3.5, 10, 1 );
	    var texture = THREE.ImageUtils.loadTexture( 'static/wood-texture.jpg' );
	    //texture.wrapS = texture.wrapT = THREE.ClampToEdgeWrapping;
	    texture.minFilter = THREE.NearestFilter;
	    var material = new THREE.MeshBasicMaterial( { map:texture, color:0xaa0000, wireframe:false});
	    var cylinder = new THREE.Mesh(geomet, material);
	    cylinder.position.set(x-2, 1.25, y-2);
	    cylinder.name = "cylinder"+x+","+y;
	    scene.add( cylinder );
	    cylinders.push(cylinder);
	}
    }
    

    //var floorTexture = new THREE.ImageUtils.loadTexture( 'static/checkerboard.jpg' );
    //floorTexture.wrapS = floorTexture.wrapT = THREE.RepeatWrapping; 
    //floorTexture.repeat.set( 3, 3 );
    // DoubleSide: render texture on both sides of mesh
    //var floorMaterial = new THREE.MeshBasicMaterial( { map: floorTexture, side: THREE.DoubleSide } );
    var floorMaterial = new THREE.MeshBasicMaterial( { color: 0x2A7E43, side: THREE.DoubleSide } );
    var floorGeometry = new THREE.PlaneBufferGeometry(10, 10, 1, 1);
    var floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.position.y = -0.5;
    floor.rotation.x = Math.PI / 2;
    floor.name = "floor";
    scene.add(floor);
    

    var skyBoxGeometry = new THREE.BoxGeometry( 10000, 10000, 10000 );
    var skyBoxMaterial = new THREE.MeshBasicMaterial( { color: 0x9999ff, side: THREE.BackSide } );
    var skyBox = new THREE.Mesh( skyBoxGeometry, skyBoxMaterial );
    scene.add(skyBox);
    
    //Light
    var light = new THREE.PointLight(0xffffff);
    light.position.set(0,250,0);
    scene.add(light);
    //var ambientLight = new THREE.AmbientLight(0x111111);
    //scene.add(ambientLight);

    // STATS
    stats = new Stats();
    stats.domElement.style.position = 'absolute';
    stats.domElement.style.bottom = '0px';
    stats.domElement.style.right = '0px';
    stats.domElement.style.zIndex = 100;
    container.appendChild( stats.domElement );    
    
    raycaster = new THREE.Raycaster();
    window.addEventListener( 'resize', onWindowResize, false );
    document.addEventListener( 'mousemove', onDocumentMouseMove, false );
    document.addEventListener( 'mousedown', onDocumentMouseDown, false );
}
    
function onWindowResize(){
    
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    
    renderer.setSize( window.innerWidth, window.innerHeight );
    

}
function onDocumentMouseMove( event ) {
    // update the mouse variable
    mouse.x = ( event.clientX / window.innerWidth ) * 2 - 1;
    mouse.y = - ( event.clientY / window.innerHeight ) * 2 + 1;
}
/*function newMove(name) {
    console.log("socket.js is not loaded yet.");
}*/
function onDocumentMouseDown( event ) 
{
    if ( INTERSECTED )
    {
	//newMove is defined in socket.js, which is loaded later
	newMove(INTERSECTED.name);
    }
}

function animate(){
    requestAnimationFrame( animate );
    render();		
    update();
}

function update(){
    var vector = new THREE.Vector3( mouse.x, mouse.y, 0.5 );
    vector.unproject(camera);
    raycaster.set( camera.position, vector.sub( camera.position ).normalize());
    var intersects = raycaster.intersectObjects( cylinders );
    
    if ( intersects.length > 0 )
    {
	// if the closest object intersected is not the currently stored intersection object
	if ( intersects[ 0 ].object != INTERSECTED ) 
	{
	    if ( INTERSECTED ) {
		INTERSECTED.material.map =  INTERSECTED.currentTexture;
		INTERSECTED.material.wireframe = false;
		INTERSECTED.material.needsUpdate = true;
	    }
	    INTERSECTED = intersects[ 0 ].object;
	    INTERSECTED.currentTexture = INTERSECTED.material.map;
	    INTERSECTED.material.map = null;
	    INTERSECTED.material.wireframe = true;
	    INTERSECTED.material.needsUpdate = true;
	}
    } 
    else // there are no intersections
    {
	if ( INTERSECTED ) {
	    INTERSECTED.material.map =  INTERSECTED.currentTexture;
	    INTERSECTED.material.wireframe = false;
	    INTERSECTED.material.needsUpdate = true;
	}
	INTERSECTED = null;
    }
    controls.update();
    stats.update();
}

var render = function () {
    renderer.render(scene, camera);
};

init();
animate();
