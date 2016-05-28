//Maya ASCII 2015ff05 scene
//Name: nhair.ma
//Last modified: Sat, Feb 14, 2015 12:53:42 AM
//Codeset: 1251
requires maya "2015ff05";
requires -nodeType "mentalrayFramebuffer" -nodeType "mentalrayOptions" -nodeType "mentalrayGlobals"
		 -nodeType "mentalrayItemsList" -dataType "byteArray" "Mayatomr" "2015.0 - 3.12.1.18 ";
requires -nodeType "RedshiftOptions" -nodeType "RedshiftArchitectural" -nodeType "RedshiftDomeLight"
		 -nodeType "RedshiftHair" "redshift4maya" "1.0.66";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2015";
fileInfo "version" "2015";
fileInfo "cutIdentifier" "201408201531-928694-1";
fileInfo "osv" "Microsoft Windows 8 Enterprise Edition, 64-bit  (Build 9200)\n";
createNode transform -s -n "persp";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 69.709507008797132 100.12851269829471 -74.09591106200395 ;
	setAttr ".r" -type "double3" -38.105266384380442 139.39999999999992 0 ;
createNode camera -s -n "perspShape" -p "persp";
	addAttr -ci true -sn "rsCameraType" -ln "rsCameraType" -min 0 -max 4 -en "Standard:Fisheye=2:Spherical:Cylindrical" 
		-at "enum";
	addAttr -ci true -sn "rsFisheyeScaleX" -ln "rsFisheyeScaleX" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeScaleY" -ln "rsFisheyeScaleY" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeAngle" -ln "rsFisheyeAngle" -dv 180 -min 1 -max 180 
		-at "double";
	addAttr -ci true -sn "rsCylindricalIsOrtho" -ln "rsCylindricalIsOrtho" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "rsCylindricalFovH" -ln "rsCylindricalFovH" -dv 360 -min 0 
		-max 360 -at "double";
	addAttr -ci true -sn "rsCylindricalFovV" -ln "rsCylindricalFovV" -dv 180 -min 0 
		-max 180 -at "double";
	addAttr -ci true -sn "rsCylindricalOrthoHeight" -ln "rsCylindricalOrthoHeight" -dv 
		100 -min 0 -max 3.4028234663852886e+038 -smn 1 -smx 500 -at "double";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsLensShader" -ln "rsLensShader" -at "message";
	addAttr -s false -ci true -m -sn "rsLensShaderList" -ln "rsLensShaderList" -at "message";
	setAttr -k off ".v" no;
	setAttr ".ovr" 1.3;
	setAttr ".fl" 34.999999999999986;
	setAttr ".ncp" 1;
	setAttr ".fcp" 100000;
	setAttr ".coi" 128.83690354272582;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 2.7539865610111747 23.988527947860945 0.99801049892280957 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
	setAttr ".dr" yes;
createNode transform -s -n "top";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 100.10000000000001 0 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
createNode camera -s -n "topShape" -p "top";
	addAttr -ci true -sn "rsCameraType" -ln "rsCameraType" -min 0 -max 4 -en "Standard:Fisheye=2:Spherical:Cylindrical" 
		-at "enum";
	addAttr -ci true -sn "rsFisheyeScaleX" -ln "rsFisheyeScaleX" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeScaleY" -ln "rsFisheyeScaleY" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeAngle" -ln "rsFisheyeAngle" -dv 180 -min 1 -max 180 
		-at "double";
	addAttr -ci true -sn "rsCylindricalIsOrtho" -ln "rsCylindricalIsOrtho" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "rsCylindricalFovH" -ln "rsCylindricalFovH" -dv 360 -min 0 
		-max 360 -at "double";
	addAttr -ci true -sn "rsCylindricalFovV" -ln "rsCylindricalFovV" -dv 180 -min 0 
		-max 180 -at "double";
	addAttr -ci true -sn "rsCylindricalOrthoHeight" -ln "rsCylindricalOrthoHeight" -dv 
		100 -min 0 -max 3.4028234663852886e+038 -smn 1 -smx 500 -at "double";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsLensShader" -ln "rsLensShader" -at "message";
	addAttr -s false -ci true -m -sn "rsLensShaderList" -ln "rsLensShaderList" -at "message";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".ncp" 1;
	setAttr ".fcp" 100000;
	setAttr ".coi" 100.10000000000001;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 100.10000000000001 ;
createNode camera -s -n "frontShape" -p "front";
	addAttr -ci true -sn "rsCameraType" -ln "rsCameraType" -min 0 -max 4 -en "Standard:Fisheye=2:Spherical:Cylindrical" 
		-at "enum";
	addAttr -ci true -sn "rsFisheyeScaleX" -ln "rsFisheyeScaleX" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeScaleY" -ln "rsFisheyeScaleY" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeAngle" -ln "rsFisheyeAngle" -dv 180 -min 1 -max 180 
		-at "double";
	addAttr -ci true -sn "rsCylindricalIsOrtho" -ln "rsCylindricalIsOrtho" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "rsCylindricalFovH" -ln "rsCylindricalFovH" -dv 360 -min 0 
		-max 360 -at "double";
	addAttr -ci true -sn "rsCylindricalFovV" -ln "rsCylindricalFovV" -dv 180 -min 0 
		-max 180 -at "double";
	addAttr -ci true -sn "rsCylindricalOrthoHeight" -ln "rsCylindricalOrthoHeight" -dv 
		100 -min 0 -max 3.4028234663852886e+038 -smn 1 -smx 500 -at "double";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsLensShader" -ln "rsLensShader" -at "message";
	addAttr -s false -ci true -m -sn "rsLensShaderList" -ln "rsLensShaderList" -at "message";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".ncp" 1;
	setAttr ".fcp" 100000;
	setAttr ".coi" 100.10000000000001;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 100.10000000000001 0 0 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
createNode camera -s -n "sideShape" -p "side";
	addAttr -ci true -sn "rsCameraType" -ln "rsCameraType" -min 0 -max 4 -en "Standard:Fisheye=2:Spherical:Cylindrical" 
		-at "enum";
	addAttr -ci true -sn "rsFisheyeScaleX" -ln "rsFisheyeScaleX" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeScaleY" -ln "rsFisheyeScaleY" -dv 1 -min 0 -max 3.4028234663852886e+038 
		-smn 0.1 -smx 10 -at "double";
	addAttr -ci true -sn "rsFisheyeAngle" -ln "rsFisheyeAngle" -dv 180 -min 1 -max 180 
		-at "double";
	addAttr -ci true -sn "rsCylindricalIsOrtho" -ln "rsCylindricalIsOrtho" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "rsCylindricalFovH" -ln "rsCylindricalFovH" -dv 360 -min 0 
		-max 360 -at "double";
	addAttr -ci true -sn "rsCylindricalFovV" -ln "rsCylindricalFovV" -dv 180 -min 0 
		-max 180 -at "double";
	addAttr -ci true -sn "rsCylindricalOrthoHeight" -ln "rsCylindricalOrthoHeight" -dv 
		100 -min 0 -max 3.4028234663852886e+038 -smn 1 -smx 500 -at "double";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsLensShader" -ln "rsLensShader" -at "message";
	addAttr -s false -ci true -m -sn "rsLensShaderList" -ln "rsLensShaderList" -at "message";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".ncp" 1;
	setAttr ".fcp" 100000;
	setAttr ".coi" 100.10000000000001;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode transform -n "pCube1";
	setAttr ".t" -type "double3" 2.7539865610111747 23.988527947860945 0.99801049892280957 ;
createNode mesh -n "pCubeShape1" -p "pCube1";
	addAttr -ci true -k true -sn "rsObjectId" -ln "rsObjectId" -min 0 -max 2147483647 
		-smn 0 -smx 100 -at "long";
	addAttr -ci true -sn "rsEnableSubdivision" -ln "rsEnableSubdivision" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "rsScreenSpaceAdaptive" -ln "rsScreenSpaceAdaptive" 
		-dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsDoSmoothSubdivision" -ln "rsDoSmoothSubdivision" 
		-dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsMinTessellationLength" -ln "rsMinTessellationLength" 
		-dv 4 -min 0 -max 3.4028234663852886e+038 -smn 0 -smx 32 -at "double";
	addAttr -ci true -k true -sn "rsMaxTessellationSubdivs" -ln "rsMaxTessellationSubdivs" 
		-dv 6 -min 0 -max 16 -at "long";
	addAttr -ci true -k true -sn "rsOutOfFrustumTessellationFactor" -ln "rsOutOfFrustumTessellationFactor" 
		-dv 4 -min 0 -max 3.4028234663852886e+038 -smn 0 -smx 32 -at "double";
	addAttr -ci true -sn "rsSubdivisionRule" -ln "rsSubdivisionRule" -min 0 -max 1 -en 
		"Catmull-Clark + Loop:Catmull-Clark Only" -at "enum";
	addAttr -ci true -sn "rsEnableDisplacement" -ln "rsEnableDisplacement" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "rsMaxDisplacement" -ln "rsMaxDisplacement" -dv 1 -min 
		0 -max 3.4028234663852886e+038 -smn 0 -smx 1000 -at "double";
	addAttr -ci true -k true -sn "rsDisplacementScale" -ln "rsDisplacementScale" -dv 
		1 -min 0 -max 3.4028234663852886e+038 -smn 0 -smx 1000 -at "double";
	addAttr -ci true -sn "rsEnableVisibilityOverrides" -ln "rsEnableVisibilityOverrides" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsPrimaryRayVisible" -ln "rsPrimaryRayVisible" -dv 
		1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsSecondaryRayVisible" -ln "rsSecondaryRayVisible" 
		-dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsShadowCaster" -ln "rsShadowCaster" -dv 1 -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "rsShadowReceiver" -ln "rsShadowReceiver" -dv 1 -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsReflectionCaster" -ln "rsReflectionCaster" -dv 1 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsReflectionVisible" -ln "rsReflectionVisible" -dv 
		1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsRefractionCaster" -ln "rsRefractionCaster" -dv 1 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsRefractionVisible" -ln "rsRefractionVisible" -dv 
		1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsGiCaster" -ln "rsGiCaster" -dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsGiVisible" -ln "rsGiVisible" -dv 1 -min 0 -max 1 
		-at "bool";
	addAttr -ci true -k true -sn "rsCausticCaster" -ln "rsCausticCaster" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "rsCausticVisible" -ln "rsCausticVisible" -dv 1 -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsFgCaster" -ln "rsFgCaster" -dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsFgVisible" -ln "rsFgVisible" -dv 1 -min 0 -max 1 
		-at "bool";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".pv" -type "double2" 0.5 0.5 ;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ds" no;
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr ".db" yes;
	setAttr ".vbc" no;
	setAttr ".ai_translator" -type "string" "polymesh";
	setAttr ".rsEnableVisibilityOverrides" yes;
createNode mesh -n "polySurfaceShape1" -p "pCube1";
	addAttr -ci true -k true -sn "rsObjectId" -ln "rsObjectId" -min 0 -max 2147483647 
		-smn 0 -smx 100 -at "long";
	addAttr -ci true -sn "rsEnableSubdivision" -ln "rsEnableSubdivision" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "rsScreenSpaceAdaptive" -ln "rsScreenSpaceAdaptive" 
		-dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsDoSmoothSubdivision" -ln "rsDoSmoothSubdivision" 
		-dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsMinTessellationLength" -ln "rsMinTessellationLength" 
		-dv 4 -min 0 -max 3.4028234663852886e+038 -smn 0 -smx 32 -at "double";
	addAttr -ci true -k true -sn "rsMaxTessellationSubdivs" -ln "rsMaxTessellationSubdivs" 
		-dv 6 -min 0 -max 16 -at "long";
	addAttr -ci true -k true -sn "rsOutOfFrustumTessellationFactor" -ln "rsOutOfFrustumTessellationFactor" 
		-dv 4 -min 0 -max 3.4028234663852886e+038 -smn 0 -smx 32 -at "double";
	addAttr -ci true -sn "rsSubdivisionRule" -ln "rsSubdivisionRule" -min 0 -max 1 -en 
		"Catmull-Clark + Loop:Catmull-Clark Only" -at "enum";
	addAttr -ci true -sn "rsEnableDisplacement" -ln "rsEnableDisplacement" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "rsMaxDisplacement" -ln "rsMaxDisplacement" -dv 1 -min 
		0 -max 3.4028234663852886e+038 -smn 0 -smx 1000 -at "double";
	addAttr -ci true -k true -sn "rsDisplacementScale" -ln "rsDisplacementScale" -dv 
		1 -min 0 -max 3.4028234663852886e+038 -smn 0 -smx 1000 -at "double";
	addAttr -ci true -sn "rsEnableVisibilityOverrides" -ln "rsEnableVisibilityOverrides" 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsPrimaryRayVisible" -ln "rsPrimaryRayVisible" -dv 
		1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsSecondaryRayVisible" -ln "rsSecondaryRayVisible" 
		-dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsShadowCaster" -ln "rsShadowCaster" -dv 1 -min 0 
		-max 1 -at "bool";
	addAttr -ci true -k true -sn "rsShadowReceiver" -ln "rsShadowReceiver" -dv 1 -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsReflectionCaster" -ln "rsReflectionCaster" -dv 1 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsReflectionVisible" -ln "rsReflectionVisible" -dv 
		1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsRefractionCaster" -ln "rsRefractionCaster" -dv 1 
		-min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsRefractionVisible" -ln "rsRefractionVisible" -dv 
		1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsGiCaster" -ln "rsGiCaster" -dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsGiVisible" -ln "rsGiVisible" -dv 1 -min 0 -max 1 
		-at "bool";
	addAttr -ci true -k true -sn "rsCausticCaster" -ln "rsCausticCaster" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -k true -sn "rsCausticVisible" -ln "rsCausticVisible" -dv 1 -min 
		0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsFgCaster" -ln "rsFgCaster" -dv 1 -min 0 -max 1 -at "bool";
	addAttr -ci true -k true -sn "rsFgVisible" -ln "rsFgVisible" -dv 1 -min 0 -max 1 
		-at "bool";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".ds" no;
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 8 ".vt[0:7]"  -23.9885273 -23.9885273 23.9885273 23.9885273 -23.9885273 23.9885273
		 -23.9885273 23.9885273 23.9885273 23.9885273 23.9885273 23.9885273 -23.9885273 23.9885273 -23.9885273
		 23.9885273 23.9885273 -23.9885273 -23.9885273 -23.9885273 -23.9885273 23.9885273 -23.9885273 -23.9885273;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 4 5 0 6 7 0 0 2 0 1 3 0 2 4 0
		 3 5 0 4 6 0 5 7 0 6 0 0 7 1 0;
	setAttr -s 6 -ch 24 ".fc[0:5]" -type "polyFaces" 
		f 4 0 5 -2 -5
		mu 0 4 0 1 3 2
		f 4 1 7 -3 -7
		mu 0 4 2 3 5 4
		f 4 2 9 -4 -9
		mu 0 4 4 5 7 6
		f 4 3 11 -1 -11
		mu 0 4 6 7 9 8
		f 4 -12 -10 -8 -6
		mu 0 4 1 10 11 3
		f 4 10 4 6 8
		mu 0 4 12 0 2 13;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
	setAttr ".db" yes;
	setAttr ".vbc" no;
createNode transform -n "hairSystem1";
createNode hairSystem -n "hairSystemShape1" -p "hairSystem1";
	addAttr -s false -ci true -sn "rsHairShader" -ln "rsHairShader" -at "message";
	addAttr -ci true -sn "rsObjectId" -ln "rsObjectId" -min 0 -max 2147483647 -smn 0 
		-smx 100 -at "long";
	setAttr -k off ".v";
	setAttr -s 138 ".ih";
	setAttr ".scd" yes;
	setAttr ".evo" 0;
	setAttr ".sfn" 0.1;
	setAttr -s 2 ".sts[0:1]"  0 1 1 1 0.2 1;
	setAttr -s 2 ".ats[0:1]"  0 1 1 1 0.2 1;
	setAttr ".ssg" 2;
	setAttr ".cwd" 8.435754186354119;
	setAttr -s 2 ".cws[0:1]"  0 0.60000002 2 1 0.41999999 3;
	setAttr ".clc[0]"  0 0.5 1;
	setAttr ".cfl[0]"  0 0 1;
	setAttr ".hwd" 0.2;
	setAttr -s 2 ".hws[0:1]"  0.14782609 0.56 1 1 0.2 1;
	setAttr -s 3 ".hcs";
	setAttr ".hcs[0].hcsp" 0;
	setAttr ".hcs[0].hcsc" -type "float3" 0.5 0.5 0.5 ;
	setAttr ".hcs[0].hcsi" 1;
	setAttr ".hcs[1].hcsp" 0.30000001192092896;
	setAttr ".hcs[1].hcsc" -type "float3" 0.80000001 0.80000001 0.80000001 ;
	setAttr ".hcs[1].hcsi" 1;
	setAttr ".hcs[2].hcsp" 1;
	setAttr ".hcs[2].hcsc" -type "float3" 1 1 1 ;
	setAttr ".hcs[2].hcsi" 1;
	setAttr ".hpc" 100;
	setAttr ".thn" 0.81379310379511327;
	setAttr ".dsc[0]"  0 1 1;
	setAttr ".actv" yes;
	setAttr -s 138 ".oh";
createNode transform -n "hairSystem1Follicles";
createNode transform -n "pCube1Follicle1205" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape1205" -p "pCube1Follicle1205";
	setAttr -k off ".v";
	setAttr ".pu" 0.125;
	setAttr ".pv" 0.05;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve1" -p "pCube1Follicle1205";
createNode nurbsCurve -n "curveShape1" -p "curve1";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle1215" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape1215" -p "pCube1Follicle1215";
	setAttr -k off ".v";
	setAttr ".pu" 0.125;
	setAttr ".pv" 0.15;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve3" -p "pCube1Follicle1215";
createNode nurbsCurve -n "curveShape3" -p "curve3";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle1225" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape1225" -p "pCube1Follicle1225";
	setAttr -k off ".v";
	setAttr ".pu" 0.125;
	setAttr ".pv" 0.25;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve5" -p "pCube1Follicle1225";
createNode nurbsCurve -n "curveShape5" -p "curve5";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle1704" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape1704" -p "pCube1Follicle1704";
	setAttr -k off ".v";
	setAttr ".pu" 0.175;
	setAttr ".pv" 0.041666666666666664;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve7" -p "pCube1Follicle1704";
createNode nurbsCurve -n "curveShape7" -p "curve7";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle1712" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape1712" -p "pCube1Follicle1712";
	setAttr -k off ".v";
	setAttr ".pu" 0.175;
	setAttr ".pv" 0.125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve9" -p "pCube1Follicle1712";
createNode nurbsCurve -n "curveShape9" -p "curve9";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle1721" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape1721" -p "pCube1Follicle1721";
	setAttr -k off ".v";
	setAttr ".pu" 0.175;
	setAttr ".pv" 0.20833333333333334;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve11" -p "pCube1Follicle1721";
createNode nurbsCurve -n "curveShape11" -p "curve11";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle2204" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape2204" -p "pCube1Follicle2204";
	setAttr -k off ".v";
	setAttr ".pu" 0.225;
	setAttr ".pv" 0.038461538461538464;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve13" -p "pCube1Follicle2204";
createNode nurbsCurve -n "curveShape13" -p "curve13";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle2211" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape2211" -p "pCube1Follicle2211";
	setAttr -k off ".v";
	setAttr ".pu" 0.225;
	setAttr ".pv" 0.11538461538461539;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve15" -p "pCube1Follicle2211";
createNode nurbsCurve -n "curveShape15" -p "curve15";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle2219" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape2219" -p "pCube1Follicle2219";
	setAttr -k off ".v";
	setAttr ".pu" 0.225;
	setAttr ".pv" 0.19230769230769232;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve17" -p "pCube1Follicle2219";
createNode nurbsCurve -n "curveShape17" -p "curve17";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle2704" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape2704" -p "pCube1Follicle2704";
	setAttr -k off ".v";
	setAttr ".pu" 0.275;
	setAttr ".pv" 0.038461538461538464;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve19" -p "pCube1Follicle2704";
createNode nurbsCurve -n "curveShape19" -p "curve19";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle2711" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape2711" -p "pCube1Follicle2711";
	setAttr -k off ".v";
	setAttr ".pu" 0.275;
	setAttr ".pv" 0.11538461538461539;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve21" -p "pCube1Follicle2711";
createNode nurbsCurve -n "curveShape21" -p "curve21";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle2719" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape2719" -p "pCube1Follicle2719";
	setAttr -k off ".v";
	setAttr ".pu" 0.275;
	setAttr ".pv" 0.19230769230769232;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve23" -p "pCube1Follicle2719";
createNode nurbsCurve -n "curveShape23" -p "curve23";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3204" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3204" -p "pCube1Follicle3204";
	setAttr -k off ".v";
	setAttr ".pu" 0.325;
	setAttr ".pv" 0.041666666666666664;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve25" -p "pCube1Follicle3204";
createNode nurbsCurve -n "curveShape25" -p "curve25";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3212" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3212" -p "pCube1Follicle3212";
	setAttr -k off ".v";
	setAttr ".pu" 0.325;
	setAttr ".pv" 0.125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve27" -p "pCube1Follicle3212";
createNode nurbsCurve -n "curveShape27" -p "curve27";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3221" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3221" -p "pCube1Follicle3221";
	setAttr -k off ".v";
	setAttr ".pu" 0.325;
	setAttr ".pv" 0.20833333333333334;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve29" -p "pCube1Follicle3221";
createNode nurbsCurve -n "curveShape29" -p "curve29";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3703" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3703" -p "pCube1Follicle3703";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.03125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve31" -p "pCube1Follicle3703";
createNode nurbsCurve -n "curveShape31" -p "curve31";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3709" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3709" -p "pCube1Follicle3709";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.09375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve33" -p "pCube1Follicle3709";
createNode nurbsCurve -n "curveShape33" -p "curve33";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3715" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3715" -p "pCube1Follicle3715";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.15625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve35" -p "pCube1Follicle3715";
createNode nurbsCurve -n "curveShape35" -p "curve35";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3722" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3722" -p "pCube1Follicle3722";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.21875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve37" -p "pCube1Follicle3722";
createNode nurbsCurve -n "curveShape37" -p "curve37";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3728" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3728" -p "pCube1Follicle3728";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.28125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve39" -p "pCube1Follicle3728";
createNode nurbsCurve -n "curveShape39" -p "curve39";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3734" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3734" -p "pCube1Follicle3734";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.34375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve41" -p "pCube1Follicle3734";
createNode nurbsCurve -n "curveShape41" -p "curve41";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3740" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3740" -p "pCube1Follicle3740";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.40625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve43" -p "pCube1Follicle3740";
createNode nurbsCurve -n "curveShape43" -p "curve43";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3746" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3746" -p "pCube1Follicle3746";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.46875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve45" -p "pCube1Follicle3746";
createNode nurbsCurve -n "curveShape45" -p "curve45";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3753" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3753" -p "pCube1Follicle3753";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.53125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve47" -p "pCube1Follicle3753";
createNode nurbsCurve -n "curveShape47" -p "curve47";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3759" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3759" -p "pCube1Follicle3759";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.59375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve49" -p "pCube1Follicle3759";
createNode nurbsCurve -n "curveShape49" -p "curve49";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3765" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3765" -p "pCube1Follicle3765";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.65625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve51" -p "pCube1Follicle3765";
createNode nurbsCurve -n "curveShape51" -p "curve51";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3771" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3771" -p "pCube1Follicle3771";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.71875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve53" -p "pCube1Follicle3771";
createNode nurbsCurve -n "curveShape53" -p "curve53";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3777" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3777" -p "pCube1Follicle3777";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.78125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve55" -p "pCube1Follicle3777";
createNode nurbsCurve -n "curveShape55" -p "curve55";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3784" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3784" -p "pCube1Follicle3784";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.84375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve57" -p "pCube1Follicle3784";
createNode nurbsCurve -n "curveShape57" -p "curve57";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3790" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3790" -p "pCube1Follicle3790";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.90625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve59" -p "pCube1Follicle3790";
createNode nurbsCurve -n "curveShape59" -p "curve59";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle3796" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape3796" -p "pCube1Follicle3796";
	setAttr -k off ".v";
	setAttr ".pu" 0.375;
	setAttr ".pv" 0.96875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve61" -p "pCube1Follicle3796";
createNode nurbsCurve -n "curveShape61" -p "curve61";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4203" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4203" -p "pCube1Follicle4203";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.027777777777777776;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve63" -p "pCube1Follicle4203";
createNode nurbsCurve -n "curveShape63" -p "curve63";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4208" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4208" -p "pCube1Follicle4208";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.083333333333333329;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve65" -p "pCube1Follicle4208";
createNode nurbsCurve -n "curveShape65" -p "curve65";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4214" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4214" -p "pCube1Follicle4214";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.1388888888888889;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve67" -p "pCube1Follicle4214";
createNode nurbsCurve -n "curveShape67" -p "curve67";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4219" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4219" -p "pCube1Follicle4219";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.19444444444444445;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve69" -p "pCube1Follicle4219";
createNode nurbsCurve -n "curveShape69" -p "curve69";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4225" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4225" -p "pCube1Follicle4225";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.25;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve71" -p "pCube1Follicle4225";
createNode nurbsCurve -n "curveShape71" -p "curve71";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4230" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4230" -p "pCube1Follicle4230";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.30555555555555558;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve73" -p "pCube1Follicle4230";
createNode nurbsCurve -n "curveShape73" -p "curve73";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4236" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4236" -p "pCube1Follicle4236";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.3611111111111111;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve75" -p "pCube1Follicle4236";
createNode nurbsCurve -n "curveShape75" -p "curve75";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4241" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4241" -p "pCube1Follicle4241";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.41666666666666669;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve77" -p "pCube1Follicle4241";
createNode nurbsCurve -n "curveShape77" -p "curve77";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4247" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4247" -p "pCube1Follicle4247";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.47222222222222221;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve79" -p "pCube1Follicle4247";
createNode nurbsCurve -n "curveShape79" -p "curve79";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4252" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4252" -p "pCube1Follicle4252";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.52777777777777779;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve81" -p "pCube1Follicle4252";
createNode nurbsCurve -n "curveShape81" -p "curve81";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4258" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4258" -p "pCube1Follicle4258";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.58333333333333337;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve83" -p "pCube1Follicle4258";
createNode nurbsCurve -n "curveShape83" -p "curve83";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4263" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4263" -p "pCube1Follicle4263";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.63888888888888884;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve85" -p "pCube1Follicle4263";
createNode nurbsCurve -n "curveShape85" -p "curve85";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4269" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4269" -p "pCube1Follicle4269";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.69444444444444442;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve87" -p "pCube1Follicle4269";
createNode nurbsCurve -n "curveShape87" -p "curve87";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4274" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4274" -p "pCube1Follicle4274";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.75;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve89" -p "pCube1Follicle4274";
createNode nurbsCurve -n "curveShape89" -p "curve89";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4280" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4280" -p "pCube1Follicle4280";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.80555555555555558;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve91" -p "pCube1Follicle4280";
createNode nurbsCurve -n "curveShape91" -p "curve91";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4285" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4285" -p "pCube1Follicle4285";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.86111111111111116;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve93" -p "pCube1Follicle4285";
createNode nurbsCurve -n "curveShape93" -p "curve93";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4291" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4291" -p "pCube1Follicle4291";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.91666666666666663;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve95" -p "pCube1Follicle4291";
createNode nurbsCurve -n "curveShape95" -p "curve95";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4296" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4296" -p "pCube1Follicle4296";
	setAttr -k off ".v";
	setAttr ".pu" 0.425;
	setAttr ".pv" 0.97222222222222221;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve97" -p "pCube1Follicle4296";
createNode nurbsCurve -n "curveShape97" -p "curve97";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4702" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4702" -p "pCube1Follicle4702";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.025;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve99" -p "pCube1Follicle4702";
createNode nurbsCurve -n "curveShape99" -p "curve99";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4707" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4707" -p "pCube1Follicle4707";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.075;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve101" -p "pCube1Follicle4707";
createNode nurbsCurve -n "curveShape101" -p "curve101";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4712" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4712" -p "pCube1Follicle4712";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve103" -p "pCube1Follicle4712";
createNode nurbsCurve -n "curveShape103" -p "curve103";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4717" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4717" -p "pCube1Follicle4717";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.175;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve105" -p "pCube1Follicle4717";
createNode nurbsCurve -n "curveShape105" -p "curve105";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4722" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4722" -p "pCube1Follicle4722";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.225;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve107" -p "pCube1Follicle4722";
createNode nurbsCurve -n "curveShape107" -p "curve107";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4727" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4727" -p "pCube1Follicle4727";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.275;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve109" -p "pCube1Follicle4727";
createNode nurbsCurve -n "curveShape109" -p "curve109";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4732" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4732" -p "pCube1Follicle4732";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.325;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve111" -p "pCube1Follicle4732";
createNode nurbsCurve -n "curveShape111" -p "curve111";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4737" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4737" -p "pCube1Follicle4737";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve113" -p "pCube1Follicle4737";
createNode nurbsCurve -n "curveShape113" -p "curve113";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4742" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4742" -p "pCube1Follicle4742";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.425;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve115" -p "pCube1Follicle4742";
createNode nurbsCurve -n "curveShape115" -p "curve115";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4747" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4747" -p "pCube1Follicle4747";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.475;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve117" -p "pCube1Follicle4747";
createNode nurbsCurve -n "curveShape117" -p "curve117";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4752" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4752" -p "pCube1Follicle4752";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.525;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve119" -p "pCube1Follicle4752";
createNode nurbsCurve -n "curveShape119" -p "curve119";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4757" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4757" -p "pCube1Follicle4757";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.575;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve121" -p "pCube1Follicle4757";
createNode nurbsCurve -n "curveShape121" -p "curve121";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4762" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4762" -p "pCube1Follicle4762";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve123" -p "pCube1Follicle4762";
createNode nurbsCurve -n "curveShape123" -p "curve123";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4767" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4767" -p "pCube1Follicle4767";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.675;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve125" -p "pCube1Follicle4767";
createNode nurbsCurve -n "curveShape125" -p "curve125";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4772" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4772" -p "pCube1Follicle4772";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.725;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve127" -p "pCube1Follicle4772";
createNode nurbsCurve -n "curveShape127" -p "curve127";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4777" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4777" -p "pCube1Follicle4777";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.775;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve129" -p "pCube1Follicle4777";
createNode nurbsCurve -n "curveShape129" -p "curve129";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4782" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4782" -p "pCube1Follicle4782";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.825;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve131" -p "pCube1Follicle4782";
createNode nurbsCurve -n "curveShape131" -p "curve131";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4787" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4787" -p "pCube1Follicle4787";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve133" -p "pCube1Follicle4787";
createNode nurbsCurve -n "curveShape133" -p "curve133";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4792" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4792" -p "pCube1Follicle4792";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.925;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve135" -p "pCube1Follicle4792";
createNode nurbsCurve -n "curveShape135" -p "curve135";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle4797" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape4797" -p "pCube1Follicle4797";
	setAttr -k off ".v";
	setAttr ".pu" 0.475;
	setAttr ".pv" 0.975;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve137" -p "pCube1Follicle4797";
createNode nurbsCurve -n "curveShape137" -p "curve137";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5202" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5202" -p "pCube1Follicle5202";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.025;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve139" -p "pCube1Follicle5202";
createNode nurbsCurve -n "curveShape139" -p "curve139";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5207" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5207" -p "pCube1Follicle5207";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.075;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve141" -p "pCube1Follicle5207";
createNode nurbsCurve -n "curveShape141" -p "curve141";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5212" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5212" -p "pCube1Follicle5212";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve143" -p "pCube1Follicle5212";
createNode nurbsCurve -n "curveShape143" -p "curve143";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5217" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5217" -p "pCube1Follicle5217";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.175;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve145" -p "pCube1Follicle5217";
createNode nurbsCurve -n "curveShape145" -p "curve145";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5222" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5222" -p "pCube1Follicle5222";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.225;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve147" -p "pCube1Follicle5222";
createNode nurbsCurve -n "curveShape147" -p "curve147";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5227" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5227" -p "pCube1Follicle5227";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.275;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve149" -p "pCube1Follicle5227";
createNode nurbsCurve -n "curveShape149" -p "curve149";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5232" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5232" -p "pCube1Follicle5232";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.325;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve151" -p "pCube1Follicle5232";
createNode nurbsCurve -n "curveShape151" -p "curve151";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5237" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5237" -p "pCube1Follicle5237";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve153" -p "pCube1Follicle5237";
createNode nurbsCurve -n "curveShape153" -p "curve153";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5242" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5242" -p "pCube1Follicle5242";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.425;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve155" -p "pCube1Follicle5242";
createNode nurbsCurve -n "curveShape155" -p "curve155";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5247" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5247" -p "pCube1Follicle5247";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.475;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve157" -p "pCube1Follicle5247";
createNode nurbsCurve -n "curveShape157" -p "curve157";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5252" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5252" -p "pCube1Follicle5252";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.525;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve159" -p "pCube1Follicle5252";
createNode nurbsCurve -n "curveShape159" -p "curve159";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5257" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5257" -p "pCube1Follicle5257";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.575;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve161" -p "pCube1Follicle5257";
createNode nurbsCurve -n "curveShape161" -p "curve161";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5262" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5262" -p "pCube1Follicle5262";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve163" -p "pCube1Follicle5262";
createNode nurbsCurve -n "curveShape163" -p "curve163";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5267" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5267" -p "pCube1Follicle5267";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.675;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve165" -p "pCube1Follicle5267";
createNode nurbsCurve -n "curveShape165" -p "curve165";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5272" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5272" -p "pCube1Follicle5272";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.725;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve167" -p "pCube1Follicle5272";
createNode nurbsCurve -n "curveShape167" -p "curve167";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5277" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5277" -p "pCube1Follicle5277";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.775;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve169" -p "pCube1Follicle5277";
createNode nurbsCurve -n "curveShape169" -p "curve169";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5282" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5282" -p "pCube1Follicle5282";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.825;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve171" -p "pCube1Follicle5282";
createNode nurbsCurve -n "curveShape171" -p "curve171";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5287" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5287" -p "pCube1Follicle5287";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve173" -p "pCube1Follicle5287";
createNode nurbsCurve -n "curveShape173" -p "curve173";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5292" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5292" -p "pCube1Follicle5292";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.925;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve175" -p "pCube1Follicle5292";
createNode nurbsCurve -n "curveShape175" -p "curve175";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5297" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5297" -p "pCube1Follicle5297";
	setAttr -k off ".v";
	setAttr ".pu" 0.525;
	setAttr ".pv" 0.975;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve177" -p "pCube1Follicle5297";
createNode nurbsCurve -n "curveShape177" -p "curve177";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5703" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5703" -p "pCube1Follicle5703";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.027777777777777776;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve179" -p "pCube1Follicle5703";
createNode nurbsCurve -n "curveShape179" -p "curve179";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5708" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5708" -p "pCube1Follicle5708";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.083333333333333329;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve181" -p "pCube1Follicle5708";
createNode nurbsCurve -n "curveShape181" -p "curve181";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5714" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5714" -p "pCube1Follicle5714";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.1388888888888889;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve183" -p "pCube1Follicle5714";
createNode nurbsCurve -n "curveShape183" -p "curve183";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5719" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5719" -p "pCube1Follicle5719";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.19444444444444445;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve185" -p "pCube1Follicle5719";
createNode nurbsCurve -n "curveShape185" -p "curve185";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5725" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5725" -p "pCube1Follicle5725";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.25;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve187" -p "pCube1Follicle5725";
createNode nurbsCurve -n "curveShape187" -p "curve187";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5730" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5730" -p "pCube1Follicle5730";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.30555555555555558;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve189" -p "pCube1Follicle5730";
createNode nurbsCurve -n "curveShape189" -p "curve189";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5736" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5736" -p "pCube1Follicle5736";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.3611111111111111;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve191" -p "pCube1Follicle5736";
createNode nurbsCurve -n "curveShape191" -p "curve191";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5741" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5741" -p "pCube1Follicle5741";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.41666666666666669;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve193" -p "pCube1Follicle5741";
createNode nurbsCurve -n "curveShape193" -p "curve193";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5747" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5747" -p "pCube1Follicle5747";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.47222222222222221;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve195" -p "pCube1Follicle5747";
createNode nurbsCurve -n "curveShape195" -p "curve195";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5752" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5752" -p "pCube1Follicle5752";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.52777777777777779;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve197" -p "pCube1Follicle5752";
createNode nurbsCurve -n "curveShape197" -p "curve197";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5758" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5758" -p "pCube1Follicle5758";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.58333333333333337;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve199" -p "pCube1Follicle5758";
createNode nurbsCurve -n "curveShape199" -p "curve199";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5763" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5763" -p "pCube1Follicle5763";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.63888888888888884;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve201" -p "pCube1Follicle5763";
createNode nurbsCurve -n "curveShape201" -p "curve201";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5769" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5769" -p "pCube1Follicle5769";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.69444444444444442;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve203" -p "pCube1Follicle5769";
createNode nurbsCurve -n "curveShape203" -p "curve203";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5774" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5774" -p "pCube1Follicle5774";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.75;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve205" -p "pCube1Follicle5774";
createNode nurbsCurve -n "curveShape205" -p "curve205";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5780" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5780" -p "pCube1Follicle5780";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.80555555555555558;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve207" -p "pCube1Follicle5780";
createNode nurbsCurve -n "curveShape207" -p "curve207";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5785" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5785" -p "pCube1Follicle5785";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.86111111111111116;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve209" -p "pCube1Follicle5785";
createNode nurbsCurve -n "curveShape209" -p "curve209";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5791" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5791" -p "pCube1Follicle5791";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.91666666666666663;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve211" -p "pCube1Follicle5791";
createNode nurbsCurve -n "curveShape211" -p "curve211";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle5796" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape5796" -p "pCube1Follicle5796";
	setAttr -k off ".v";
	setAttr ".pu" 0.575;
	setAttr ".pv" 0.97222222222222221;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve213" -p "pCube1Follicle5796";
createNode nurbsCurve -n "curveShape213" -p "curve213";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6203" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6203" -p "pCube1Follicle6203";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.03125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve215" -p "pCube1Follicle6203";
createNode nurbsCurve -n "curveShape215" -p "curve215";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6209" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6209" -p "pCube1Follicle6209";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.09375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve217" -p "pCube1Follicle6209";
createNode nurbsCurve -n "curveShape217" -p "curve217";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6215" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6215" -p "pCube1Follicle6215";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.15625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve219" -p "pCube1Follicle6215";
createNode nurbsCurve -n "curveShape219" -p "curve219";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6222" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6222" -p "pCube1Follicle6222";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.21875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve221" -p "pCube1Follicle6222";
createNode nurbsCurve -n "curveShape221" -p "curve221";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6228" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6228" -p "pCube1Follicle6228";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.28125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve223" -p "pCube1Follicle6228";
createNode nurbsCurve -n "curveShape223" -p "curve223";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6234" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6234" -p "pCube1Follicle6234";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.34375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve225" -p "pCube1Follicle6234";
createNode nurbsCurve -n "curveShape225" -p "curve225";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6240" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6240" -p "pCube1Follicle6240";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.40625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve227" -p "pCube1Follicle6240";
createNode nurbsCurve -n "curveShape227" -p "curve227";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6246" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6246" -p "pCube1Follicle6246";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.46875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve229" -p "pCube1Follicle6246";
createNode nurbsCurve -n "curveShape229" -p "curve229";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6253" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6253" -p "pCube1Follicle6253";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.53125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve231" -p "pCube1Follicle6253";
createNode nurbsCurve -n "curveShape231" -p "curve231";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6259" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6259" -p "pCube1Follicle6259";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.59375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve233" -p "pCube1Follicle6259";
createNode nurbsCurve -n "curveShape233" -p "curve233";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6265" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6265" -p "pCube1Follicle6265";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.65625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve235" -p "pCube1Follicle6265";
createNode nurbsCurve -n "curveShape235" -p "curve235";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6271" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6271" -p "pCube1Follicle6271";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.71875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve237" -p "pCube1Follicle6271";
createNode nurbsCurve -n "curveShape237" -p "curve237";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6277" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6277" -p "pCube1Follicle6277";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.78125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve239" -p "pCube1Follicle6277";
createNode nurbsCurve -n "curveShape239" -p "curve239";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6284" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6284" -p "pCube1Follicle6284";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.84375;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve241" -p "pCube1Follicle6284";
createNode nurbsCurve -n "curveShape241" -p "curve241";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6290" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6290" -p "pCube1Follicle6290";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.90625;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve243" -p "pCube1Follicle6290";
createNode nurbsCurve -n "curveShape243" -p "curve243";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6296" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6296" -p "pCube1Follicle6296";
	setAttr -k off ".v";
	setAttr ".pu" 0.625;
	setAttr ".pv" 0.96875;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve245" -p "pCube1Follicle6296";
createNode nurbsCurve -n "curveShape245" -p "curve245";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6704" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6704" -p "pCube1Follicle6704";
	setAttr -k off ".v";
	setAttr ".pu" 0.675;
	setAttr ".pv" 0.041666666666666664;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve247" -p "pCube1Follicle6704";
createNode nurbsCurve -n "curveShape247" -p "curve247";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6712" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6712" -p "pCube1Follicle6712";
	setAttr -k off ".v";
	setAttr ".pu" 0.675;
	setAttr ".pv" 0.125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve249" -p "pCube1Follicle6712";
createNode nurbsCurve -n "curveShape249" -p "curve249";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle6721" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape6721" -p "pCube1Follicle6721";
	setAttr -k off ".v";
	setAttr ".pu" 0.675;
	setAttr ".pv" 0.20833333333333334;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve251" -p "pCube1Follicle6721";
createNode nurbsCurve -n "curveShape251" -p "curve251";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle7204" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape7204" -p "pCube1Follicle7204";
	setAttr -k off ".v";
	setAttr ".pu" 0.725;
	setAttr ".pv" 0.038461538461538464;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve253" -p "pCube1Follicle7204";
createNode nurbsCurve -n "curveShape253" -p "curve253";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle7211" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape7211" -p "pCube1Follicle7211";
	setAttr -k off ".v";
	setAttr ".pu" 0.725;
	setAttr ".pv" 0.11538461538461539;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve255" -p "pCube1Follicle7211";
createNode nurbsCurve -n "curveShape255" -p "curve255";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle7219" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape7219" -p "pCube1Follicle7219";
	setAttr -k off ".v";
	setAttr ".pu" 0.725;
	setAttr ".pv" 0.19230769230769232;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve257" -p "pCube1Follicle7219";
createNode nurbsCurve -n "curveShape257" -p "curve257";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle7704" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape7704" -p "pCube1Follicle7704";
	setAttr -k off ".v";
	setAttr ".pu" 0.775;
	setAttr ".pv" 0.038461538461538464;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve259" -p "pCube1Follicle7704";
createNode nurbsCurve -n "curveShape259" -p "curve259";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle7711" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape7711" -p "pCube1Follicle7711";
	setAttr -k off ".v";
	setAttr ".pu" 0.775;
	setAttr ".pv" 0.11538461538461539;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve261" -p "pCube1Follicle7711";
createNode nurbsCurve -n "curveShape261" -p "curve261";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle7719" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape7719" -p "pCube1Follicle7719";
	setAttr -k off ".v";
	setAttr ".pu" 0.775;
	setAttr ".pv" 0.19230769230769232;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve263" -p "pCube1Follicle7719";
createNode nurbsCurve -n "curveShape263" -p "curve263";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle8204" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape8204" -p "pCube1Follicle8204";
	setAttr -k off ".v";
	setAttr ".pu" 0.825;
	setAttr ".pv" 0.041666666666666664;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve265" -p "pCube1Follicle8204";
createNode nurbsCurve -n "curveShape265" -p "curve265";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle8212" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape8212" -p "pCube1Follicle8212";
	setAttr -k off ".v";
	setAttr ".pu" 0.825;
	setAttr ".pv" 0.125;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve267" -p "pCube1Follicle8212";
createNode nurbsCurve -n "curveShape267" -p "curve267";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle8221" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape8221" -p "pCube1Follicle8221";
	setAttr -k off ".v";
	setAttr ".pu" 0.825;
	setAttr ".pv" 0.20833333333333334;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve269" -p "pCube1Follicle8221";
createNode nurbsCurve -n "curveShape269" -p "curve269";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle8705" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape8705" -p "pCube1Follicle8705";
	setAttr -k off ".v";
	setAttr ".pu" 0.875;
	setAttr ".pv" 0.05;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve271" -p "pCube1Follicle8705";
createNode nurbsCurve -n "curveShape271" -p "curve271";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle8715" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape8715" -p "pCube1Follicle8715";
	setAttr -k off ".v";
	setAttr ".pu" 0.875;
	setAttr ".pv" 0.15;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve273" -p "pCube1Follicle8715";
createNode nurbsCurve -n "curveShape273" -p "curve273";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "pCube1Follicle8725" -p "hairSystem1Follicles";
createNode follicle -n "pCube1FollicleShape8725" -p "pCube1Follicle8725";
	setAttr -k off ".v";
	setAttr ".pu" 0.875;
	setAttr ".pv" 0.25;
	setAttr -s 2 ".sts[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".cws[0:1]"  0 1 3 1 0.2 3;
	setAttr -s 2 ".ats[0:1]"  0 1 3 1 0.2 3;
createNode transform -n "curve275" -p "pCube1Follicle8725";
createNode nurbsCurve -n "curveShape275" -p "curve275";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 9 0 no 3
		10 0 1 2 3 4 5 6 7 8 9
		10
		0 0 0
		0 0 1.867611111
		0 0 3.735222222
		0 0 5.6028333330000004
		0 0 7.470444444
		0 0 9.3380555560000005
		0 0 11.205666669999999
		0 0 13.07327778
		0 0 14.94088889
		0 0 16.808499999999999
		;
createNode transform -n "hairSystem1OutputCurves";
createNode transform -n "curve2" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape2" -p "curve2";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve4" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape4" -p "curve4";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve6" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape6" -p "curve6";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve8" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape8" -p "curve8";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve10" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape10" -p "curve10";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve12" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape12" -p "curve12";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve14" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape14" -p "curve14";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve16" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape16" -p "curve16";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve18" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape18" -p "curve18";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve20" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape20" -p "curve20";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve22" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape22" -p "curve22";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve24" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape24" -p "curve24";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve26" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape26" -p "curve26";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve28" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape28" -p "curve28";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve30" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape30" -p "curve30";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve32" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape32" -p "curve32";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve34" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape34" -p "curve34";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve36" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape36" -p "curve36";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve38" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape38" -p "curve38";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve40" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape40" -p "curve40";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve42" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape42" -p "curve42";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve44" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape44" -p "curve44";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve46" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape46" -p "curve46";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve48" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape48" -p "curve48";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve50" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape50" -p "curve50";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve52" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape52" -p "curve52";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve54" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape54" -p "curve54";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve56" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape56" -p "curve56";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve58" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape58" -p "curve58";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve60" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape60" -p "curve60";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve62" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape62" -p "curve62";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve64" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape64" -p "curve64";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve66" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape66" -p "curve66";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve68" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape68" -p "curve68";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve70" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape70" -p "curve70";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve72" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape72" -p "curve72";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve74" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape74" -p "curve74";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve76" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape76" -p "curve76";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve78" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape78" -p "curve78";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve80" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape80" -p "curve80";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve82" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape82" -p "curve82";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve84" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape84" -p "curve84";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve86" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape86" -p "curve86";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve88" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape88" -p "curve88";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve90" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape90" -p "curve90";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve92" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape92" -p "curve92";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve94" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape94" -p "curve94";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve96" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape96" -p "curve96";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve98" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape98" -p "curve98";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve100" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape100" -p "curve100";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve102" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape102" -p "curve102";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve104" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape104" -p "curve104";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve106" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape106" -p "curve106";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve108" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape108" -p "curve108";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve110" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape110" -p "curve110";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve112" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape112" -p "curve112";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve114" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape114" -p "curve114";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve116" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape116" -p "curve116";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve118" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape118" -p "curve118";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve120" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape120" -p "curve120";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve122" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape122" -p "curve122";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve124" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape124" -p "curve124";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve126" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape126" -p "curve126";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve128" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape128" -p "curve128";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve130" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape130" -p "curve130";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve132" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape132" -p "curve132";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve134" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape134" -p "curve134";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve136" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape136" -p "curve136";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve138" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape138" -p "curve138";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve140" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape140" -p "curve140";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve142" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape142" -p "curve142";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve144" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape144" -p "curve144";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve146" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape146" -p "curve146";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve148" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape148" -p "curve148";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve150" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape150" -p "curve150";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve152" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape152" -p "curve152";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve154" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape154" -p "curve154";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve156" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape156" -p "curve156";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve158" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape158" -p "curve158";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve160" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape160" -p "curve160";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve162" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape162" -p "curve162";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve164" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape164" -p "curve164";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve166" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape166" -p "curve166";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve168" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape168" -p "curve168";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve170" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape170" -p "curve170";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve172" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape172" -p "curve172";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve174" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape174" -p "curve174";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve176" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape176" -p "curve176";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve178" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape178" -p "curve178";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve180" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape180" -p "curve180";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve182" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape182" -p "curve182";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve184" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape184" -p "curve184";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve186" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape186" -p "curve186";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve188" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape188" -p "curve188";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve190" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape190" -p "curve190";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve192" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape192" -p "curve192";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve194" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape194" -p "curve194";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve196" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape196" -p "curve196";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve198" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape198" -p "curve198";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve200" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape200" -p "curve200";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve202" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape202" -p "curve202";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve204" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape204" -p "curve204";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve206" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape206" -p "curve206";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve208" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape208" -p "curve208";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve210" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape210" -p "curve210";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve212" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape212" -p "curve212";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve214" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape214" -p "curve214";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve216" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape216" -p "curve216";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve218" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape218" -p "curve218";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve220" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape220" -p "curve220";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve222" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape222" -p "curve222";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve224" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape224" -p "curve224";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve226" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape226" -p "curve226";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve228" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape228" -p "curve228";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve230" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape230" -p "curve230";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve232" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape232" -p "curve232";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve234" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape234" -p "curve234";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve236" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape236" -p "curve236";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve238" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape238" -p "curve238";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve240" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape240" -p "curve240";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve242" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape242" -p "curve242";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve244" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape244" -p "curve244";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve246" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape246" -p "curve246";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve248" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape248" -p "curve248";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve250" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape250" -p "curve250";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve252" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape252" -p "curve252";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve254" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape254" -p "curve254";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve256" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape256" -p "curve256";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve258" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape258" -p "curve258";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve260" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape260" -p "curve260";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve262" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape262" -p "curve262";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve264" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape264" -p "curve264";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve266" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape266" -p "curve266";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve268" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape268" -p "curve268";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve270" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape270" -p "curve270";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve272" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape272" -p "curve272";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve274" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape274" -p "curve274";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "curve276" -p "hairSystem1OutputCurves";
createNode nurbsCurve -n "curveShape276" -p "curve276";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr ".tw" yes;
createNode transform -n "pfxHair1";
createNode pfxHair -n "pfxHairShape1" -p "pfxHair1";
	setAttr -k off ".v";
	setAttr ".dpc" 100;
	setAttr ".dam" no;
	setAttr ".dgr" 4;
createNode nucleus -n "nucleus1";
createNode transform -n "redshiftDomeLight1";
	setAttr ".r" -type "double3" 0 90 0 ;
createNode RedshiftDomeLight -n "redshiftDomeLightShape1" -p "redshiftDomeLight1";
	setAttr -k off ".v";
	setAttr ".tex0" -type "string" "D:/Work/ThePirate/hdri/day.hdr";
createNode lightLinker -s -n "lightLinker1";
	setAttr -s 4 ".lnk";
	setAttr -s 4 ".slnk";
createNode mentalrayItemsList -s -n "mentalrayItemsList";
createNode mentalrayGlobals -s -n "mentalrayGlobals";
	setAttr ".rvb" 3;
	setAttr ".ivb" no;
createNode mentalrayOptions -s -n "miDefaultOptions";
	addAttr -ci true -m -sn "stringOptions" -ln "stringOptions" -at "compound" -nc 
		3;
	addAttr -ci true -sn "name" -ln "name" -dt "string" -p "stringOptions";
	addAttr -ci true -sn "value" -ln "value" -dt "string" -p "stringOptions";
	addAttr -ci true -sn "type" -ln "type" -dt "string" -p "stringOptions";
	setAttr ".maxr" 400;
	setAttr ".shrd" 50;
	setAttr -s 48 ".stringOptions";
	setAttr ".stringOptions[0].name" -type "string" "rast motion factor";
	setAttr ".stringOptions[0].value" -type "string" "1.0";
	setAttr ".stringOptions[0].type" -type "string" "scalar";
	setAttr ".stringOptions[1].name" -type "string" "rast transparency depth";
	setAttr ".stringOptions[1].value" -type "string" "40";
	setAttr ".stringOptions[1].type" -type "string" "integer";
	setAttr ".stringOptions[2].name" -type "string" "rast useopacity";
	setAttr ".stringOptions[2].value" -type "string" "true";
	setAttr ".stringOptions[2].type" -type "string" "boolean";
	setAttr ".stringOptions[3].name" -type "string" "importon";
	setAttr ".stringOptions[3].value" -type "string" "false";
	setAttr ".stringOptions[3].type" -type "string" "boolean";
	setAttr ".stringOptions[4].name" -type "string" "importon density";
	setAttr ".stringOptions[4].value" -type "string" "1.0";
	setAttr ".stringOptions[4].type" -type "string" "scalar";
	setAttr ".stringOptions[5].name" -type "string" "importon merge";
	setAttr ".stringOptions[5].value" -type "string" "0.0";
	setAttr ".stringOptions[5].type" -type "string" "scalar";
	setAttr ".stringOptions[6].name" -type "string" "importon trace depth";
	setAttr ".stringOptions[6].value" -type "string" "0";
	setAttr ".stringOptions[6].type" -type "string" "integer";
	setAttr ".stringOptions[7].name" -type "string" "importon traverse";
	setAttr ".stringOptions[7].value" -type "string" "true";
	setAttr ".stringOptions[7].type" -type "string" "boolean";
	setAttr ".stringOptions[8].name" -type "string" "shadowmap pixel samples";
	setAttr ".stringOptions[8].value" -type "string" "3";
	setAttr ".stringOptions[8].type" -type "string" "integer";
	setAttr ".stringOptions[9].name" -type "string" "ambient occlusion";
	setAttr ".stringOptions[9].value" -type "string" "false";
	setAttr ".stringOptions[9].type" -type "string" "boolean";
	setAttr ".stringOptions[10].name" -type "string" "ambient occlusion rays";
	setAttr ".stringOptions[10].value" -type "string" "64";
	setAttr ".stringOptions[10].type" -type "string" "integer";
	setAttr ".stringOptions[11].name" -type "string" "ambient occlusion cache";
	setAttr ".stringOptions[11].value" -type "string" "false";
	setAttr ".stringOptions[11].type" -type "string" "boolean";
	setAttr ".stringOptions[12].name" -type "string" "ambient occlusion cache density";
	setAttr ".stringOptions[12].value" -type "string" "1.0";
	setAttr ".stringOptions[12].type" -type "string" "scalar";
	setAttr ".stringOptions[13].name" -type "string" "ambient occlusion cache points";
	setAttr ".stringOptions[13].value" -type "string" "64";
	setAttr ".stringOptions[13].type" -type "string" "integer";
	setAttr ".stringOptions[14].name" -type "string" "irradiance particles";
	setAttr ".stringOptions[14].value" -type "string" "false";
	setAttr ".stringOptions[14].type" -type "string" "boolean";
	setAttr ".stringOptions[15].name" -type "string" "irradiance particles rays";
	setAttr ".stringOptions[15].value" -type "string" "256";
	setAttr ".stringOptions[15].type" -type "string" "integer";
	setAttr ".stringOptions[16].name" -type "string" "irradiance particles interpolate";
	setAttr ".stringOptions[16].value" -type "string" "1";
	setAttr ".stringOptions[16].type" -type "string" "integer";
	setAttr ".stringOptions[17].name" -type "string" "irradiance particles interppoints";
	setAttr ".stringOptions[17].value" -type "string" "64";
	setAttr ".stringOptions[17].type" -type "string" "integer";
	setAttr ".stringOptions[18].name" -type "string" "irradiance particles indirect passes";
	setAttr ".stringOptions[18].value" -type "string" "0";
	setAttr ".stringOptions[18].type" -type "string" "integer";
	setAttr ".stringOptions[19].name" -type "string" "irradiance particles scale";
	setAttr ".stringOptions[19].value" -type "string" "1.0";
	setAttr ".stringOptions[19].type" -type "string" "scalar";
	setAttr ".stringOptions[20].name" -type "string" "irradiance particles env";
	setAttr ".stringOptions[20].value" -type "string" "true";
	setAttr ".stringOptions[20].type" -type "string" "boolean";
	setAttr ".stringOptions[21].name" -type "string" "irradiance particles env rays";
	setAttr ".stringOptions[21].value" -type "string" "256";
	setAttr ".stringOptions[21].type" -type "string" "integer";
	setAttr ".stringOptions[22].name" -type "string" "irradiance particles env scale";
	setAttr ".stringOptions[22].value" -type "string" "1";
	setAttr ".stringOptions[22].type" -type "string" "integer";
	setAttr ".stringOptions[23].name" -type "string" "irradiance particles rebuild";
	setAttr ".stringOptions[23].value" -type "string" "true";
	setAttr ".stringOptions[23].type" -type "string" "boolean";
	setAttr ".stringOptions[24].name" -type "string" "irradiance particles file";
	setAttr ".stringOptions[24].value" -type "string" "";
	setAttr ".stringOptions[24].type" -type "string" "string";
	setAttr ".stringOptions[25].name" -type "string" "geom displace motion factor";
	setAttr ".stringOptions[25].value" -type "string" "1.0";
	setAttr ".stringOptions[25].type" -type "string" "scalar";
	setAttr ".stringOptions[26].name" -type "string" "contrast all buffers";
	setAttr ".stringOptions[26].value" -type "string" "true";
	setAttr ".stringOptions[26].type" -type "string" "boolean";
	setAttr ".stringOptions[27].name" -type "string" "finalgather normal tolerance";
	setAttr ".stringOptions[27].value" -type "string" "25.842";
	setAttr ".stringOptions[27].type" -type "string" "scalar";
	setAttr ".stringOptions[28].name" -type "string" "trace camera clip";
	setAttr ".stringOptions[28].value" -type "string" "false";
	setAttr ".stringOptions[28].type" -type "string" "boolean";
	setAttr ".stringOptions[29].name" -type "string" "unified sampling";
	setAttr ".stringOptions[29].value" -type "string" "true";
	setAttr ".stringOptions[29].type" -type "string" "boolean";
	setAttr ".stringOptions[30].name" -type "string" "samples quality";
	setAttr ".stringOptions[30].value" -type "string" "0.25 0.25 0.25 0.25";
	setAttr ".stringOptions[30].type" -type "string" "color";
	setAttr ".stringOptions[31].name" -type "string" "samples min";
	setAttr ".stringOptions[31].value" -type "string" "1.0";
	setAttr ".stringOptions[31].type" -type "string" "scalar";
	setAttr ".stringOptions[32].name" -type "string" "samples max";
	setAttr ".stringOptions[32].value" -type "string" "100";
	setAttr ".stringOptions[32].type" -type "string" "scalar";
	setAttr ".stringOptions[33].name" -type "string" "samples error cutoff";
	setAttr ".stringOptions[33].value" -type "string" "0.0 0.0 0.0 0.0";
	setAttr ".stringOptions[33].type" -type "string" "color";
	setAttr ".stringOptions[34].name" -type "string" "samples per object";
	setAttr ".stringOptions[34].value" -type "string" "false";
	setAttr ".stringOptions[34].type" -type "string" "boolean";
	setAttr ".stringOptions[35].name" -type "string" "progressive";
	setAttr ".stringOptions[35].value" -type "string" "false";
	setAttr ".stringOptions[35].type" -type "string" "boolean";
	setAttr ".stringOptions[36].name" -type "string" "progressive max time";
	setAttr ".stringOptions[36].value" -type "string" "0";
	setAttr ".stringOptions[36].type" -type "string" "integer";
	setAttr ".stringOptions[37].name" -type "string" "progressive subsampling size";
	setAttr ".stringOptions[37].value" -type "string" "4";
	setAttr ".stringOptions[37].type" -type "string" "integer";
	setAttr ".stringOptions[38].name" -type "string" "iray";
	setAttr ".stringOptions[38].value" -type "string" "false";
	setAttr ".stringOptions[38].type" -type "string" "boolean";
	setAttr ".stringOptions[39].name" -type "string" "light relative scale";
	setAttr ".stringOptions[39].value" -type "string" "0.31831";
	setAttr ".stringOptions[39].type" -type "string" "scalar";
	setAttr ".stringOptions[40].name" -type "string" "trace camera motion vectors";
	setAttr ".stringOptions[40].value" -type "string" "false";
	setAttr ".stringOptions[40].type" -type "string" "boolean";
	setAttr ".stringOptions[41].name" -type "string" "ray differentials";
	setAttr ".stringOptions[41].value" -type "string" "true";
	setAttr ".stringOptions[41].type" -type "string" "boolean";
	setAttr ".stringOptions[42].name" -type "string" "environment lighting mode";
	setAttr ".stringOptions[42].value" -type "string" "off";
	setAttr ".stringOptions[42].type" -type "string" "string";
	setAttr ".stringOptions[43].name" -type "string" "environment lighting quality";
	setAttr ".stringOptions[43].value" -type "string" "0.2";
	setAttr ".stringOptions[43].type" -type "string" "scalar";
	setAttr ".stringOptions[44].name" -type "string" "environment lighting shadow";
	setAttr ".stringOptions[44].value" -type "string" "transparent";
	setAttr ".stringOptions[44].type" -type "string" "string";
	setAttr ".stringOptions[45].name" -type "string" "environment lighting resolution";
	setAttr ".stringOptions[45].value" -type "string" "512";
	setAttr ".stringOptions[45].type" -type "string" "integer";
	setAttr ".stringOptions[46].name" -type "string" "environment lighting shader samples";
	setAttr ".stringOptions[46].value" -type "string" "2";
	setAttr ".stringOptions[46].type" -type "string" "integer";
	setAttr ".stringOptions[47].name" -type "string" "environment lighting scale";
	setAttr ".stringOptions[47].value" -type "string" "1.0 1.0 1.0";
	setAttr ".stringOptions[47].type" -type "string" "color";
createNode mentalrayFramebuffer -s -n "miDefaultFramebuffer";
createNode displayLayerManager -n "layerManager";
createNode displayLayer -n "defaultLayer";
createNode renderLayerManager -n "renderLayerManager";
createNode renderLayer -n "defaultRenderLayer";
	setAttr ".g" yes;
createNode polySmoothFace -n "polySmoothFace1";
	setAttr ".ics" -type "componentList" 1 "f[*]";
	setAttr ".sdt" 2;
	setAttr ".dv" 3;
	setAttr ".suv" yes;
	setAttr ".kb" no;
	setAttr ".ksb" no;
	setAttr ".kmb" 0;
	setAttr ".kt" no;
	setAttr ".ps" 0.10000000149011612;
	setAttr ".ro" 1;
	setAttr ".ma" yes;
	setAttr ".m08" yes;
createNode RedshiftArchitectural -n "redshiftArchitectural1";
	setAttr ".diffuse_weight" 0.5;
	setAttr ".reflectivity" 0;
createNode shadingEngine -n "redshiftArchitectural1SG";
	addAttr -s false -ci true -sn "rsSurfaceShader" -ln "rsSurfaceShader" -at "message";
	addAttr -s false -ci true -sn "rsShadowShader" -ln "rsShadowShader" -at "message";
	addAttr -s false -ci true -sn "rsPhotonShader" -ln "rsPhotonShader" -at "message";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsBumpmapShader" -ln "rsBumpmapShader" -at "message";
	addAttr -s false -ci true -sn "rsDisplacementShader" -ln "rsDisplacementShader" 
		-at "message";
	addAttr -ci true -sn "rsMaterialId" -ln "rsMaterialId" -min 0 -max 2147483647 -smn 
		0 -smx 100 -at "long";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo1";
createNode RedshiftOptions -s -n "redshiftOptions";
createNode RedshiftHair -n "redshiftHair1";
createNode shadingEngine -n "redshiftHair1SG";
	addAttr -s false -ci true -sn "rsSurfaceShader" -ln "rsSurfaceShader" -at "message";
	addAttr -s false -ci true -sn "rsShadowShader" -ln "rsShadowShader" -at "message";
	addAttr -s false -ci true -sn "rsPhotonShader" -ln "rsPhotonShader" -at "message";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsBumpmapShader" -ln "rsBumpmapShader" -at "message";
	addAttr -s false -ci true -sn "rsDisplacementShader" -ln "rsDisplacementShader" 
		-at "message";
	addAttr -ci true -sn "rsMaterialId" -ln "rsMaterialId" -min 0 -max 2147483647 -smn 
		0 -smx 100 -at "long";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo2";
createNode script -n "sceneConfigurationScriptNode";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 150 -ast 1 -aet 150 ";
	setAttr ".st" 6;
select -ne :time1;
	setAttr -av -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr ".o" 120;
	setAttr ".unw" 120;
select -ne :renderPartition;
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 4 ".st";
	setAttr -k on ".an";
	setAttr -k on ".pt";
select -ne :renderGlobalsList1;
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :defaultShaderList1;
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 4 ".s";
select -ne :postProcessList1;
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
select -ne :lightList1;
select -ne :initialShadingGroup;
	addAttr -s false -ci true -sn "rsSurfaceShader" -ln "rsSurfaceShader" -at "message";
	addAttr -s false -ci true -sn "rsShadowShader" -ln "rsShadowShader" -at "message";
	addAttr -s false -ci true -sn "rsPhotonShader" -ln "rsPhotonShader" -at "message";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsBumpmapShader" -ln "rsBumpmapShader" -at "message";
	addAttr -s false -ci true -sn "rsDisplacementShader" -ln "rsDisplacementShader" 
		-at "message";
	addAttr -ci true -sn "rsMaterialId" -ln "rsMaterialId" -min 0 -max 2147483647 -smn 
		0 -smx 100 -at "long";
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".mwc";
	setAttr -k on ".an";
	setAttr -k on ".il";
	setAttr -k on ".vo";
	setAttr -k on ".eo";
	setAttr -k on ".fo";
	setAttr -k on ".epo";
	setAttr ".ro" yes;
	setAttr -cb on ".mimt";
	setAttr -cb on ".miop";
	setAttr -cb on ".mise";
	setAttr -cb on ".mism";
	setAttr -cb on ".mice";
	setAttr -av -cb on ".micc";
	setAttr -cb on ".mica";
	setAttr -cb on ".micw";
	setAttr -cb on ".mirw";
select -ne :initialParticleSE;
	addAttr -s false -ci true -sn "rsSurfaceShader" -ln "rsSurfaceShader" -at "message";
	addAttr -s false -ci true -sn "rsShadowShader" -ln "rsShadowShader" -at "message";
	addAttr -s false -ci true -sn "rsPhotonShader" -ln "rsPhotonShader" -at "message";
	addAttr -s false -ci true -sn "rsEnvironmentShader" -ln "rsEnvironmentShader" -at "message";
	addAttr -s false -ci true -sn "rsBumpmapShader" -ln "rsBumpmapShader" -at "message";
	addAttr -s false -ci true -sn "rsDisplacementShader" -ln "rsDisplacementShader" 
		-at "message";
	addAttr -ci true -sn "rsMaterialId" -ln "rsMaterialId" -min 0 -max 2147483647 -smn 
		0 -smx 100 -at "long";
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".mwc";
	setAttr -k on ".an";
	setAttr -k on ".il";
	setAttr -k on ".vo";
	setAttr -k on ".eo";
	setAttr -k on ".fo";
	setAttr -k on ".epo";
	setAttr ".ro" yes;
	setAttr -cb on ".mimt";
	setAttr -cb on ".miop";
	setAttr -cb on ".mise";
	setAttr -cb on ".mism";
	setAttr -cb on ".mice";
	setAttr -av -cb on ".micc";
	setAttr -cb on ".mica";
	setAttr -cb on ".micw";
	setAttr -cb on ".mirw";
select -ne :defaultRenderGlobals;
	addAttr -ci true -sn "shave_old_preRenderMel" -ln "shave_old_preRenderMel" -dt "string";
	addAttr -ci true -sn "shave_old_postRenderMel" -ln "shave_old_postRenderMel" -dt "string";
	setAttr ".ren" -type "string" "redshift";
	setAttr ".prm" -type "string" "";
	setAttr ".pom" -type "string" "";
	setAttr ".shave_old_preRenderMel" -type "string" "";
	setAttr ".shave_old_postRenderMel" -type "string" "";
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :defaultLightSet;
	setAttr -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -k on ".nds";
	setAttr -k on ".bnm";
	setAttr -k on ".mwc";
	setAttr -k on ".an";
	setAttr -k on ".il";
	setAttr -k on ".vo";
	setAttr -k on ".eo";
	setAttr -k on ".fo";
	setAttr -k on ".epo";
select -ne :defaultColorMgtGlobals;
	setAttr ".vtn" -type "string" "sRGB gamma";
	setAttr ".wsn" -type "string" "scene-linear Rec 709/sRGB";
	setAttr ".din" -type "string" "sRGB";
	setAttr ".otn" -type "string" "sRGB gamma";
select -ne :hardwareRenderGlobals;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
	setAttr -k off ".fbfm";
	setAttr -k off -cb on ".ehql";
	setAttr -k off -cb on ".eams";
	setAttr -k off -cb on ".eeaa";
	setAttr -k off -cb on ".engm";
	setAttr -k off -cb on ".mes";
	setAttr -k off -cb on ".emb";
	setAttr -av -k off -cb on ".mbbf";
	setAttr -k off -cb on ".mbs";
	setAttr -k off -cb on ".trm";
	setAttr -k off -cb on ".tshc";
	setAttr -k off ".enpt";
	setAttr -k off -cb on ".clmt";
	setAttr -k off -cb on ".tcov";
	setAttr -k off -cb on ".lith";
	setAttr -k off -cb on ".sobc";
	setAttr -k off -cb on ".cuth";
	setAttr -k off -cb on ".hgcd";
	setAttr -k off -cb on ".hgci";
	setAttr -k off -cb on ".mgcs";
	setAttr -k off -cb on ".twa";
	setAttr -k off -cb on ".twz";
	setAttr -k on ".hwcc";
	setAttr -k on ".hwdp";
	setAttr -k on ".hwql";
	setAttr -k on ".hwfr";
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
select -ne :defaultHardwareRenderGlobals;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".rp";
	setAttr -k on ".cai";
	setAttr -k on ".coi";
	setAttr -cb on ".bc";
	setAttr -av -k on ".bcb";
	setAttr -av -k on ".bcg";
	setAttr -av -k on ".bcr";
	setAttr -k on ".ei";
	setAttr -k on ".ex";
	setAttr -av -k on ".es";
	setAttr -av -k on ".ef";
	setAttr -av -k on ".bf";
	setAttr -k on ".fii";
	setAttr -av -k on ".sf";
	setAttr -k on ".gr";
	setAttr -k on ".li";
	setAttr -k on ".ls";
	setAttr -k on ".mb";
	setAttr -k on ".ti";
	setAttr -k on ".txt";
	setAttr -k on ".mpr";
	setAttr -k on ".wzd";
	setAttr -k on ".if";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
	setAttr -k on ".as";
	setAttr -k on ".ds";
	setAttr -k on ".lm";
	setAttr -k on ".fir";
	setAttr -k on ".aap";
	setAttr -k on ".gh";
	setAttr -cb on ".sd";
connectAttr "polySmoothFace1.out" "pCubeShape1.i";
connectAttr ":time1.o" "hairSystemShape1.cti";
connectAttr "pCube1FollicleShape1205.oha" "hairSystemShape1.ih[0]";
connectAttr "pCube1FollicleShape1215.oha" "hairSystemShape1.ih[1]";
connectAttr "pCube1FollicleShape1225.oha" "hairSystemShape1.ih[2]";
connectAttr "pCube1FollicleShape1704.oha" "hairSystemShape1.ih[3]";
connectAttr "pCube1FollicleShape1712.oha" "hairSystemShape1.ih[4]";
connectAttr "pCube1FollicleShape1721.oha" "hairSystemShape1.ih[5]";
connectAttr "pCube1FollicleShape2204.oha" "hairSystemShape1.ih[6]";
connectAttr "pCube1FollicleShape2211.oha" "hairSystemShape1.ih[7]";
connectAttr "pCube1FollicleShape2219.oha" "hairSystemShape1.ih[8]";
connectAttr "pCube1FollicleShape2704.oha" "hairSystemShape1.ih[9]";
connectAttr "pCube1FollicleShape2711.oha" "hairSystemShape1.ih[10]";
connectAttr "pCube1FollicleShape2719.oha" "hairSystemShape1.ih[11]";
connectAttr "pCube1FollicleShape3204.oha" "hairSystemShape1.ih[12]";
connectAttr "pCube1FollicleShape3212.oha" "hairSystemShape1.ih[13]";
connectAttr "pCube1FollicleShape3221.oha" "hairSystemShape1.ih[14]";
connectAttr "pCube1FollicleShape3703.oha" "hairSystemShape1.ih[15]";
connectAttr "pCube1FollicleShape3709.oha" "hairSystemShape1.ih[16]";
connectAttr "pCube1FollicleShape3715.oha" "hairSystemShape1.ih[17]";
connectAttr "pCube1FollicleShape3722.oha" "hairSystemShape1.ih[18]";
connectAttr "pCube1FollicleShape3728.oha" "hairSystemShape1.ih[19]";
connectAttr "pCube1FollicleShape3734.oha" "hairSystemShape1.ih[20]";
connectAttr "pCube1FollicleShape3740.oha" "hairSystemShape1.ih[21]";
connectAttr "pCube1FollicleShape3746.oha" "hairSystemShape1.ih[22]";
connectAttr "pCube1FollicleShape3753.oha" "hairSystemShape1.ih[23]";
connectAttr "pCube1FollicleShape3759.oha" "hairSystemShape1.ih[24]";
connectAttr "pCube1FollicleShape3765.oha" "hairSystemShape1.ih[25]";
connectAttr "pCube1FollicleShape3771.oha" "hairSystemShape1.ih[26]";
connectAttr "pCube1FollicleShape3777.oha" "hairSystemShape1.ih[27]";
connectAttr "pCube1FollicleShape3784.oha" "hairSystemShape1.ih[28]";
connectAttr "pCube1FollicleShape3790.oha" "hairSystemShape1.ih[29]";
connectAttr "pCube1FollicleShape3796.oha" "hairSystemShape1.ih[30]";
connectAttr "pCube1FollicleShape4203.oha" "hairSystemShape1.ih[31]";
connectAttr "pCube1FollicleShape4208.oha" "hairSystemShape1.ih[32]";
connectAttr "pCube1FollicleShape4214.oha" "hairSystemShape1.ih[33]";
connectAttr "pCube1FollicleShape4219.oha" "hairSystemShape1.ih[34]";
connectAttr "pCube1FollicleShape4225.oha" "hairSystemShape1.ih[35]";
connectAttr "pCube1FollicleShape4230.oha" "hairSystemShape1.ih[36]";
connectAttr "pCube1FollicleShape4236.oha" "hairSystemShape1.ih[37]";
connectAttr "pCube1FollicleShape4241.oha" "hairSystemShape1.ih[38]";
connectAttr "pCube1FollicleShape4247.oha" "hairSystemShape1.ih[39]";
connectAttr "pCube1FollicleShape4252.oha" "hairSystemShape1.ih[40]";
connectAttr "pCube1FollicleShape4258.oha" "hairSystemShape1.ih[41]";
connectAttr "pCube1FollicleShape4263.oha" "hairSystemShape1.ih[42]";
connectAttr "pCube1FollicleShape4269.oha" "hairSystemShape1.ih[43]";
connectAttr "pCube1FollicleShape4274.oha" "hairSystemShape1.ih[44]";
connectAttr "pCube1FollicleShape4280.oha" "hairSystemShape1.ih[45]";
connectAttr "pCube1FollicleShape4285.oha" "hairSystemShape1.ih[46]";
connectAttr "pCube1FollicleShape4291.oha" "hairSystemShape1.ih[47]";
connectAttr "pCube1FollicleShape4296.oha" "hairSystemShape1.ih[48]";
connectAttr "pCube1FollicleShape4702.oha" "hairSystemShape1.ih[49]";
connectAttr "pCube1FollicleShape4707.oha" "hairSystemShape1.ih[50]";
connectAttr "pCube1FollicleShape4712.oha" "hairSystemShape1.ih[51]";
connectAttr "pCube1FollicleShape4717.oha" "hairSystemShape1.ih[52]";
connectAttr "pCube1FollicleShape4722.oha" "hairSystemShape1.ih[53]";
connectAttr "pCube1FollicleShape4727.oha" "hairSystemShape1.ih[54]";
connectAttr "pCube1FollicleShape4732.oha" "hairSystemShape1.ih[55]";
connectAttr "pCube1FollicleShape4737.oha" "hairSystemShape1.ih[56]";
connectAttr "pCube1FollicleShape4742.oha" "hairSystemShape1.ih[57]";
connectAttr "pCube1FollicleShape4747.oha" "hairSystemShape1.ih[58]";
connectAttr "pCube1FollicleShape4752.oha" "hairSystemShape1.ih[59]";
connectAttr "pCube1FollicleShape4757.oha" "hairSystemShape1.ih[60]";
connectAttr "pCube1FollicleShape4762.oha" "hairSystemShape1.ih[61]";
connectAttr "pCube1FollicleShape4767.oha" "hairSystemShape1.ih[62]";
connectAttr "pCube1FollicleShape4772.oha" "hairSystemShape1.ih[63]";
connectAttr "pCube1FollicleShape4777.oha" "hairSystemShape1.ih[64]";
connectAttr "pCube1FollicleShape4782.oha" "hairSystemShape1.ih[65]";
connectAttr "pCube1FollicleShape4787.oha" "hairSystemShape1.ih[66]";
connectAttr "pCube1FollicleShape4792.oha" "hairSystemShape1.ih[67]";
connectAttr "pCube1FollicleShape4797.oha" "hairSystemShape1.ih[68]";
connectAttr "pCube1FollicleShape5202.oha" "hairSystemShape1.ih[69]";
connectAttr "pCube1FollicleShape5207.oha" "hairSystemShape1.ih[70]";
connectAttr "pCube1FollicleShape5212.oha" "hairSystemShape1.ih[71]";
connectAttr "pCube1FollicleShape5217.oha" "hairSystemShape1.ih[72]";
connectAttr "pCube1FollicleShape5222.oha" "hairSystemShape1.ih[73]";
connectAttr "pCube1FollicleShape5227.oha" "hairSystemShape1.ih[74]";
connectAttr "pCube1FollicleShape5232.oha" "hairSystemShape1.ih[75]";
connectAttr "pCube1FollicleShape5237.oha" "hairSystemShape1.ih[76]";
connectAttr "pCube1FollicleShape5242.oha" "hairSystemShape1.ih[77]";
connectAttr "pCube1FollicleShape5247.oha" "hairSystemShape1.ih[78]";
connectAttr "pCube1FollicleShape5252.oha" "hairSystemShape1.ih[79]";
connectAttr "pCube1FollicleShape5257.oha" "hairSystemShape1.ih[80]";
connectAttr "pCube1FollicleShape5262.oha" "hairSystemShape1.ih[81]";
connectAttr "pCube1FollicleShape5267.oha" "hairSystemShape1.ih[82]";
connectAttr "pCube1FollicleShape5272.oha" "hairSystemShape1.ih[83]";
connectAttr "pCube1FollicleShape5277.oha" "hairSystemShape1.ih[84]";
connectAttr "pCube1FollicleShape5282.oha" "hairSystemShape1.ih[85]";
connectAttr "pCube1FollicleShape5287.oha" "hairSystemShape1.ih[86]";
connectAttr "pCube1FollicleShape5292.oha" "hairSystemShape1.ih[87]";
connectAttr "pCube1FollicleShape5297.oha" "hairSystemShape1.ih[88]";
connectAttr "pCube1FollicleShape5703.oha" "hairSystemShape1.ih[89]";
connectAttr "pCube1FollicleShape5708.oha" "hairSystemShape1.ih[90]";
connectAttr "pCube1FollicleShape5714.oha" "hairSystemShape1.ih[91]";
connectAttr "pCube1FollicleShape5719.oha" "hairSystemShape1.ih[92]";
connectAttr "pCube1FollicleShape5725.oha" "hairSystemShape1.ih[93]";
connectAttr "pCube1FollicleShape5730.oha" "hairSystemShape1.ih[94]";
connectAttr "pCube1FollicleShape5736.oha" "hairSystemShape1.ih[95]";
connectAttr "pCube1FollicleShape5741.oha" "hairSystemShape1.ih[96]";
connectAttr "pCube1FollicleShape5747.oha" "hairSystemShape1.ih[97]";
connectAttr "pCube1FollicleShape5752.oha" "hairSystemShape1.ih[98]";
connectAttr "pCube1FollicleShape5758.oha" "hairSystemShape1.ih[99]";
connectAttr "pCube1FollicleShape5763.oha" "hairSystemShape1.ih[100]";
connectAttr "pCube1FollicleShape5769.oha" "hairSystemShape1.ih[101]";
connectAttr "pCube1FollicleShape5774.oha" "hairSystemShape1.ih[102]";
connectAttr "pCube1FollicleShape5780.oha" "hairSystemShape1.ih[103]";
connectAttr "pCube1FollicleShape5785.oha" "hairSystemShape1.ih[104]";
connectAttr "pCube1FollicleShape5791.oha" "hairSystemShape1.ih[105]";
connectAttr "pCube1FollicleShape5796.oha" "hairSystemShape1.ih[106]";
connectAttr "pCube1FollicleShape6203.oha" "hairSystemShape1.ih[107]";
connectAttr "pCube1FollicleShape6209.oha" "hairSystemShape1.ih[108]";
connectAttr "pCube1FollicleShape6215.oha" "hairSystemShape1.ih[109]";
connectAttr "pCube1FollicleShape6222.oha" "hairSystemShape1.ih[110]";
connectAttr "pCube1FollicleShape6228.oha" "hairSystemShape1.ih[111]";
connectAttr "pCube1FollicleShape6234.oha" "hairSystemShape1.ih[112]";
connectAttr "pCube1FollicleShape6240.oha" "hairSystemShape1.ih[113]";
connectAttr "pCube1FollicleShape6246.oha" "hairSystemShape1.ih[114]";
connectAttr "pCube1FollicleShape6253.oha" "hairSystemShape1.ih[115]";
connectAttr "pCube1FollicleShape6259.oha" "hairSystemShape1.ih[116]";
connectAttr "pCube1FollicleShape6265.oha" "hairSystemShape1.ih[117]";
connectAttr "pCube1FollicleShape6271.oha" "hairSystemShape1.ih[118]";
connectAttr "pCube1FollicleShape6277.oha" "hairSystemShape1.ih[119]";
connectAttr "pCube1FollicleShape6284.oha" "hairSystemShape1.ih[120]";
connectAttr "pCube1FollicleShape6290.oha" "hairSystemShape1.ih[121]";
connectAttr "pCube1FollicleShape6296.oha" "hairSystemShape1.ih[122]";
connectAttr "pCube1FollicleShape6704.oha" "hairSystemShape1.ih[123]";
connectAttr "pCube1FollicleShape6712.oha" "hairSystemShape1.ih[124]";
connectAttr "pCube1FollicleShape6721.oha" "hairSystemShape1.ih[125]";
connectAttr "pCube1FollicleShape7204.oha" "hairSystemShape1.ih[126]";
connectAttr "pCube1FollicleShape7211.oha" "hairSystemShape1.ih[127]";
connectAttr "pCube1FollicleShape7219.oha" "hairSystemShape1.ih[128]";
connectAttr "pCube1FollicleShape7704.oha" "hairSystemShape1.ih[129]";
connectAttr "pCube1FollicleShape7711.oha" "hairSystemShape1.ih[130]";
connectAttr "pCube1FollicleShape7719.oha" "hairSystemShape1.ih[131]";
connectAttr "pCube1FollicleShape8204.oha" "hairSystemShape1.ih[132]";
connectAttr "pCube1FollicleShape8212.oha" "hairSystemShape1.ih[133]";
connectAttr "pCube1FollicleShape8221.oha" "hairSystemShape1.ih[134]";
connectAttr "pCube1FollicleShape8705.oha" "hairSystemShape1.ih[135]";
connectAttr "pCube1FollicleShape8715.oha" "hairSystemShape1.ih[136]";
connectAttr "pCube1FollicleShape8725.oha" "hairSystemShape1.ih[137]";
connectAttr "nucleus1.noao[0]" "hairSystemShape1.nxst";
connectAttr "nucleus1.stf" "hairSystemShape1.stf";
connectAttr "redshiftHair1.oc" "hairSystemShape1.rsHairShader";
connectAttr "pCube1FollicleShape1205.ot" "pCube1Follicle1205.t" -l on;
connectAttr "pCube1FollicleShape1205.or" "pCube1Follicle1205.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape1205.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape1205.inm";
connectAttr "curveShape1.l" "pCube1FollicleShape1205.sp";
connectAttr "curve1.wm" "pCube1FollicleShape1205.spm";
connectAttr "hairSystemShape1.oh[0]" "pCube1FollicleShape1205.crp";
connectAttr "pCube1FollicleShape1215.ot" "pCube1Follicle1215.t" -l on;
connectAttr "pCube1FollicleShape1215.or" "pCube1Follicle1215.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape1215.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape1215.inm";
connectAttr "curveShape3.l" "pCube1FollicleShape1215.sp";
connectAttr "curve3.wm" "pCube1FollicleShape1215.spm";
connectAttr "hairSystemShape1.oh[1]" "pCube1FollicleShape1215.crp";
connectAttr "pCube1FollicleShape1225.ot" "pCube1Follicle1225.t" -l on;
connectAttr "pCube1FollicleShape1225.or" "pCube1Follicle1225.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape1225.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape1225.inm";
connectAttr "curveShape5.l" "pCube1FollicleShape1225.sp";
connectAttr "curve5.wm" "pCube1FollicleShape1225.spm";
connectAttr "hairSystemShape1.oh[2]" "pCube1FollicleShape1225.crp";
connectAttr "pCube1FollicleShape1704.ot" "pCube1Follicle1704.t" -l on;
connectAttr "pCube1FollicleShape1704.or" "pCube1Follicle1704.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape1704.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape1704.inm";
connectAttr "curveShape7.l" "pCube1FollicleShape1704.sp";
connectAttr "curve7.wm" "pCube1FollicleShape1704.spm";
connectAttr "hairSystemShape1.oh[3]" "pCube1FollicleShape1704.crp";
connectAttr "pCube1FollicleShape1712.ot" "pCube1Follicle1712.t" -l on;
connectAttr "pCube1FollicleShape1712.or" "pCube1Follicle1712.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape1712.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape1712.inm";
connectAttr "curveShape9.l" "pCube1FollicleShape1712.sp";
connectAttr "curve9.wm" "pCube1FollicleShape1712.spm";
connectAttr "hairSystemShape1.oh[4]" "pCube1FollicleShape1712.crp";
connectAttr "pCube1FollicleShape1721.ot" "pCube1Follicle1721.t" -l on;
connectAttr "pCube1FollicleShape1721.or" "pCube1Follicle1721.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape1721.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape1721.inm";
connectAttr "curveShape11.l" "pCube1FollicleShape1721.sp";
connectAttr "curve11.wm" "pCube1FollicleShape1721.spm";
connectAttr "hairSystemShape1.oh[5]" "pCube1FollicleShape1721.crp";
connectAttr "pCube1FollicleShape2204.ot" "pCube1Follicle2204.t" -l on;
connectAttr "pCube1FollicleShape2204.or" "pCube1Follicle2204.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape2204.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape2204.inm";
connectAttr "curveShape13.l" "pCube1FollicleShape2204.sp";
connectAttr "curve13.wm" "pCube1FollicleShape2204.spm";
connectAttr "hairSystemShape1.oh[6]" "pCube1FollicleShape2204.crp";
connectAttr "pCube1FollicleShape2211.ot" "pCube1Follicle2211.t" -l on;
connectAttr "pCube1FollicleShape2211.or" "pCube1Follicle2211.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape2211.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape2211.inm";
connectAttr "curveShape15.l" "pCube1FollicleShape2211.sp";
connectAttr "curve15.wm" "pCube1FollicleShape2211.spm";
connectAttr "hairSystemShape1.oh[7]" "pCube1FollicleShape2211.crp";
connectAttr "pCube1FollicleShape2219.ot" "pCube1Follicle2219.t" -l on;
connectAttr "pCube1FollicleShape2219.or" "pCube1Follicle2219.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape2219.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape2219.inm";
connectAttr "curveShape17.l" "pCube1FollicleShape2219.sp";
connectAttr "curve17.wm" "pCube1FollicleShape2219.spm";
connectAttr "hairSystemShape1.oh[8]" "pCube1FollicleShape2219.crp";
connectAttr "pCube1FollicleShape2704.ot" "pCube1Follicle2704.t" -l on;
connectAttr "pCube1FollicleShape2704.or" "pCube1Follicle2704.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape2704.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape2704.inm";
connectAttr "curveShape19.l" "pCube1FollicleShape2704.sp";
connectAttr "curve19.wm" "pCube1FollicleShape2704.spm";
connectAttr "hairSystemShape1.oh[9]" "pCube1FollicleShape2704.crp";
connectAttr "pCube1FollicleShape2711.ot" "pCube1Follicle2711.t" -l on;
connectAttr "pCube1FollicleShape2711.or" "pCube1Follicle2711.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape2711.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape2711.inm";
connectAttr "curveShape21.l" "pCube1FollicleShape2711.sp";
connectAttr "curve21.wm" "pCube1FollicleShape2711.spm";
connectAttr "hairSystemShape1.oh[10]" "pCube1FollicleShape2711.crp";
connectAttr "pCube1FollicleShape2719.ot" "pCube1Follicle2719.t" -l on;
connectAttr "pCube1FollicleShape2719.or" "pCube1Follicle2719.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape2719.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape2719.inm";
connectAttr "curveShape23.l" "pCube1FollicleShape2719.sp";
connectAttr "curve23.wm" "pCube1FollicleShape2719.spm";
connectAttr "hairSystemShape1.oh[11]" "pCube1FollicleShape2719.crp";
connectAttr "pCube1FollicleShape3204.ot" "pCube1Follicle3204.t" -l on;
connectAttr "pCube1FollicleShape3204.or" "pCube1Follicle3204.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3204.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3204.inm";
connectAttr "curveShape25.l" "pCube1FollicleShape3204.sp";
connectAttr "curve25.wm" "pCube1FollicleShape3204.spm";
connectAttr "hairSystemShape1.oh[12]" "pCube1FollicleShape3204.crp";
connectAttr "pCube1FollicleShape3212.ot" "pCube1Follicle3212.t" -l on;
connectAttr "pCube1FollicleShape3212.or" "pCube1Follicle3212.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3212.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3212.inm";
connectAttr "curveShape27.l" "pCube1FollicleShape3212.sp";
connectAttr "curve27.wm" "pCube1FollicleShape3212.spm";
connectAttr "hairSystemShape1.oh[13]" "pCube1FollicleShape3212.crp";
connectAttr "pCube1FollicleShape3221.ot" "pCube1Follicle3221.t" -l on;
connectAttr "pCube1FollicleShape3221.or" "pCube1Follicle3221.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3221.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3221.inm";
connectAttr "curveShape29.l" "pCube1FollicleShape3221.sp";
connectAttr "curve29.wm" "pCube1FollicleShape3221.spm";
connectAttr "hairSystemShape1.oh[14]" "pCube1FollicleShape3221.crp";
connectAttr "pCube1FollicleShape3703.ot" "pCube1Follicle3703.t" -l on;
connectAttr "pCube1FollicleShape3703.or" "pCube1Follicle3703.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3703.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3703.inm";
connectAttr "curveShape31.l" "pCube1FollicleShape3703.sp";
connectAttr "curve31.wm" "pCube1FollicleShape3703.spm";
connectAttr "hairSystemShape1.oh[15]" "pCube1FollicleShape3703.crp";
connectAttr "pCube1FollicleShape3709.ot" "pCube1Follicle3709.t" -l on;
connectAttr "pCube1FollicleShape3709.or" "pCube1Follicle3709.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3709.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3709.inm";
connectAttr "curveShape33.l" "pCube1FollicleShape3709.sp";
connectAttr "curve33.wm" "pCube1FollicleShape3709.spm";
connectAttr "hairSystemShape1.oh[16]" "pCube1FollicleShape3709.crp";
connectAttr "pCube1FollicleShape3715.ot" "pCube1Follicle3715.t" -l on;
connectAttr "pCube1FollicleShape3715.or" "pCube1Follicle3715.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3715.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3715.inm";
connectAttr "curveShape35.l" "pCube1FollicleShape3715.sp";
connectAttr "curve35.wm" "pCube1FollicleShape3715.spm";
connectAttr "hairSystemShape1.oh[17]" "pCube1FollicleShape3715.crp";
connectAttr "pCube1FollicleShape3722.ot" "pCube1Follicle3722.t" -l on;
connectAttr "pCube1FollicleShape3722.or" "pCube1Follicle3722.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3722.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3722.inm";
connectAttr "curveShape37.l" "pCube1FollicleShape3722.sp";
connectAttr "curve37.wm" "pCube1FollicleShape3722.spm";
connectAttr "hairSystemShape1.oh[18]" "pCube1FollicleShape3722.crp";
connectAttr "pCube1FollicleShape3728.ot" "pCube1Follicle3728.t" -l on;
connectAttr "pCube1FollicleShape3728.or" "pCube1Follicle3728.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3728.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3728.inm";
connectAttr "curveShape39.l" "pCube1FollicleShape3728.sp";
connectAttr "curve39.wm" "pCube1FollicleShape3728.spm";
connectAttr "hairSystemShape1.oh[19]" "pCube1FollicleShape3728.crp";
connectAttr "pCube1FollicleShape3734.ot" "pCube1Follicle3734.t" -l on;
connectAttr "pCube1FollicleShape3734.or" "pCube1Follicle3734.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3734.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3734.inm";
connectAttr "curveShape41.l" "pCube1FollicleShape3734.sp";
connectAttr "curve41.wm" "pCube1FollicleShape3734.spm";
connectAttr "hairSystemShape1.oh[20]" "pCube1FollicleShape3734.crp";
connectAttr "pCube1FollicleShape3740.ot" "pCube1Follicle3740.t" -l on;
connectAttr "pCube1FollicleShape3740.or" "pCube1Follicle3740.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3740.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3740.inm";
connectAttr "curveShape43.l" "pCube1FollicleShape3740.sp";
connectAttr "curve43.wm" "pCube1FollicleShape3740.spm";
connectAttr "hairSystemShape1.oh[21]" "pCube1FollicleShape3740.crp";
connectAttr "pCube1FollicleShape3746.ot" "pCube1Follicle3746.t" -l on;
connectAttr "pCube1FollicleShape3746.or" "pCube1Follicle3746.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3746.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3746.inm";
connectAttr "curveShape45.l" "pCube1FollicleShape3746.sp";
connectAttr "curve45.wm" "pCube1FollicleShape3746.spm";
connectAttr "hairSystemShape1.oh[22]" "pCube1FollicleShape3746.crp";
connectAttr "pCube1FollicleShape3753.ot" "pCube1Follicle3753.t" -l on;
connectAttr "pCube1FollicleShape3753.or" "pCube1Follicle3753.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3753.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3753.inm";
connectAttr "curveShape47.l" "pCube1FollicleShape3753.sp";
connectAttr "curve47.wm" "pCube1FollicleShape3753.spm";
connectAttr "hairSystemShape1.oh[23]" "pCube1FollicleShape3753.crp";
connectAttr "pCube1FollicleShape3759.ot" "pCube1Follicle3759.t" -l on;
connectAttr "pCube1FollicleShape3759.or" "pCube1Follicle3759.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3759.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3759.inm";
connectAttr "curveShape49.l" "pCube1FollicleShape3759.sp";
connectAttr "curve49.wm" "pCube1FollicleShape3759.spm";
connectAttr "hairSystemShape1.oh[24]" "pCube1FollicleShape3759.crp";
connectAttr "pCube1FollicleShape3765.ot" "pCube1Follicle3765.t" -l on;
connectAttr "pCube1FollicleShape3765.or" "pCube1Follicle3765.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3765.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3765.inm";
connectAttr "curveShape51.l" "pCube1FollicleShape3765.sp";
connectAttr "curve51.wm" "pCube1FollicleShape3765.spm";
connectAttr "hairSystemShape1.oh[25]" "pCube1FollicleShape3765.crp";
connectAttr "pCube1FollicleShape3771.ot" "pCube1Follicle3771.t" -l on;
connectAttr "pCube1FollicleShape3771.or" "pCube1Follicle3771.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3771.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3771.inm";
connectAttr "curveShape53.l" "pCube1FollicleShape3771.sp";
connectAttr "curve53.wm" "pCube1FollicleShape3771.spm";
connectAttr "hairSystemShape1.oh[26]" "pCube1FollicleShape3771.crp";
connectAttr "pCube1FollicleShape3777.ot" "pCube1Follicle3777.t" -l on;
connectAttr "pCube1FollicleShape3777.or" "pCube1Follicle3777.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3777.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3777.inm";
connectAttr "curveShape55.l" "pCube1FollicleShape3777.sp";
connectAttr "curve55.wm" "pCube1FollicleShape3777.spm";
connectAttr "hairSystemShape1.oh[27]" "pCube1FollicleShape3777.crp";
connectAttr "pCube1FollicleShape3784.ot" "pCube1Follicle3784.t" -l on;
connectAttr "pCube1FollicleShape3784.or" "pCube1Follicle3784.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3784.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3784.inm";
connectAttr "curveShape57.l" "pCube1FollicleShape3784.sp";
connectAttr "curve57.wm" "pCube1FollicleShape3784.spm";
connectAttr "hairSystemShape1.oh[28]" "pCube1FollicleShape3784.crp";
connectAttr "pCube1FollicleShape3790.ot" "pCube1Follicle3790.t" -l on;
connectAttr "pCube1FollicleShape3790.or" "pCube1Follicle3790.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3790.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3790.inm";
connectAttr "curveShape59.l" "pCube1FollicleShape3790.sp";
connectAttr "curve59.wm" "pCube1FollicleShape3790.spm";
connectAttr "hairSystemShape1.oh[29]" "pCube1FollicleShape3790.crp";
connectAttr "pCube1FollicleShape3796.ot" "pCube1Follicle3796.t" -l on;
connectAttr "pCube1FollicleShape3796.or" "pCube1Follicle3796.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape3796.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape3796.inm";
connectAttr "curveShape61.l" "pCube1FollicleShape3796.sp";
connectAttr "curve61.wm" "pCube1FollicleShape3796.spm";
connectAttr "hairSystemShape1.oh[30]" "pCube1FollicleShape3796.crp";
connectAttr "pCube1FollicleShape4203.ot" "pCube1Follicle4203.t" -l on;
connectAttr "pCube1FollicleShape4203.or" "pCube1Follicle4203.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4203.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4203.inm";
connectAttr "curveShape63.l" "pCube1FollicleShape4203.sp";
connectAttr "curve63.wm" "pCube1FollicleShape4203.spm";
connectAttr "hairSystemShape1.oh[31]" "pCube1FollicleShape4203.crp";
connectAttr "pCube1FollicleShape4208.ot" "pCube1Follicle4208.t" -l on;
connectAttr "pCube1FollicleShape4208.or" "pCube1Follicle4208.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4208.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4208.inm";
connectAttr "curveShape65.l" "pCube1FollicleShape4208.sp";
connectAttr "curve65.wm" "pCube1FollicleShape4208.spm";
connectAttr "hairSystemShape1.oh[32]" "pCube1FollicleShape4208.crp";
connectAttr "pCube1FollicleShape4214.ot" "pCube1Follicle4214.t" -l on;
connectAttr "pCube1FollicleShape4214.or" "pCube1Follicle4214.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4214.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4214.inm";
connectAttr "curveShape67.l" "pCube1FollicleShape4214.sp";
connectAttr "curve67.wm" "pCube1FollicleShape4214.spm";
connectAttr "hairSystemShape1.oh[33]" "pCube1FollicleShape4214.crp";
connectAttr "pCube1FollicleShape4219.ot" "pCube1Follicle4219.t" -l on;
connectAttr "pCube1FollicleShape4219.or" "pCube1Follicle4219.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4219.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4219.inm";
connectAttr "curveShape69.l" "pCube1FollicleShape4219.sp";
connectAttr "curve69.wm" "pCube1FollicleShape4219.spm";
connectAttr "hairSystemShape1.oh[34]" "pCube1FollicleShape4219.crp";
connectAttr "pCube1FollicleShape4225.ot" "pCube1Follicle4225.t" -l on;
connectAttr "pCube1FollicleShape4225.or" "pCube1Follicle4225.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4225.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4225.inm";
connectAttr "curveShape71.l" "pCube1FollicleShape4225.sp";
connectAttr "curve71.wm" "pCube1FollicleShape4225.spm";
connectAttr "hairSystemShape1.oh[35]" "pCube1FollicleShape4225.crp";
connectAttr "pCube1FollicleShape4230.ot" "pCube1Follicle4230.t" -l on;
connectAttr "pCube1FollicleShape4230.or" "pCube1Follicle4230.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4230.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4230.inm";
connectAttr "curveShape73.l" "pCube1FollicleShape4230.sp";
connectAttr "curve73.wm" "pCube1FollicleShape4230.spm";
connectAttr "hairSystemShape1.oh[36]" "pCube1FollicleShape4230.crp";
connectAttr "pCube1FollicleShape4236.ot" "pCube1Follicle4236.t" -l on;
connectAttr "pCube1FollicleShape4236.or" "pCube1Follicle4236.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4236.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4236.inm";
connectAttr "curveShape75.l" "pCube1FollicleShape4236.sp";
connectAttr "curve75.wm" "pCube1FollicleShape4236.spm";
connectAttr "hairSystemShape1.oh[37]" "pCube1FollicleShape4236.crp";
connectAttr "pCube1FollicleShape4241.ot" "pCube1Follicle4241.t" -l on;
connectAttr "pCube1FollicleShape4241.or" "pCube1Follicle4241.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4241.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4241.inm";
connectAttr "curveShape77.l" "pCube1FollicleShape4241.sp";
connectAttr "curve77.wm" "pCube1FollicleShape4241.spm";
connectAttr "hairSystemShape1.oh[38]" "pCube1FollicleShape4241.crp";
connectAttr "pCube1FollicleShape4247.ot" "pCube1Follicle4247.t" -l on;
connectAttr "pCube1FollicleShape4247.or" "pCube1Follicle4247.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4247.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4247.inm";
connectAttr "curveShape79.l" "pCube1FollicleShape4247.sp";
connectAttr "curve79.wm" "pCube1FollicleShape4247.spm";
connectAttr "hairSystemShape1.oh[39]" "pCube1FollicleShape4247.crp";
connectAttr "pCube1FollicleShape4252.ot" "pCube1Follicle4252.t" -l on;
connectAttr "pCube1FollicleShape4252.or" "pCube1Follicle4252.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4252.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4252.inm";
connectAttr "curveShape81.l" "pCube1FollicleShape4252.sp";
connectAttr "curve81.wm" "pCube1FollicleShape4252.spm";
connectAttr "hairSystemShape1.oh[40]" "pCube1FollicleShape4252.crp";
connectAttr "pCube1FollicleShape4258.ot" "pCube1Follicle4258.t" -l on;
connectAttr "pCube1FollicleShape4258.or" "pCube1Follicle4258.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4258.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4258.inm";
connectAttr "curveShape83.l" "pCube1FollicleShape4258.sp";
connectAttr "curve83.wm" "pCube1FollicleShape4258.spm";
connectAttr "hairSystemShape1.oh[41]" "pCube1FollicleShape4258.crp";
connectAttr "pCube1FollicleShape4263.ot" "pCube1Follicle4263.t" -l on;
connectAttr "pCube1FollicleShape4263.or" "pCube1Follicle4263.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4263.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4263.inm";
connectAttr "curveShape85.l" "pCube1FollicleShape4263.sp";
connectAttr "curve85.wm" "pCube1FollicleShape4263.spm";
connectAttr "hairSystemShape1.oh[42]" "pCube1FollicleShape4263.crp";
connectAttr "pCube1FollicleShape4269.ot" "pCube1Follicle4269.t" -l on;
connectAttr "pCube1FollicleShape4269.or" "pCube1Follicle4269.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4269.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4269.inm";
connectAttr "curveShape87.l" "pCube1FollicleShape4269.sp";
connectAttr "curve87.wm" "pCube1FollicleShape4269.spm";
connectAttr "hairSystemShape1.oh[43]" "pCube1FollicleShape4269.crp";
connectAttr "pCube1FollicleShape4274.ot" "pCube1Follicle4274.t" -l on;
connectAttr "pCube1FollicleShape4274.or" "pCube1Follicle4274.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4274.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4274.inm";
connectAttr "curveShape89.l" "pCube1FollicleShape4274.sp";
connectAttr "curve89.wm" "pCube1FollicleShape4274.spm";
connectAttr "hairSystemShape1.oh[44]" "pCube1FollicleShape4274.crp";
connectAttr "pCube1FollicleShape4280.ot" "pCube1Follicle4280.t" -l on;
connectAttr "pCube1FollicleShape4280.or" "pCube1Follicle4280.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4280.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4280.inm";
connectAttr "curveShape91.l" "pCube1FollicleShape4280.sp";
connectAttr "curve91.wm" "pCube1FollicleShape4280.spm";
connectAttr "hairSystemShape1.oh[45]" "pCube1FollicleShape4280.crp";
connectAttr "pCube1FollicleShape4285.ot" "pCube1Follicle4285.t" -l on;
connectAttr "pCube1FollicleShape4285.or" "pCube1Follicle4285.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4285.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4285.inm";
connectAttr "curveShape93.l" "pCube1FollicleShape4285.sp";
connectAttr "curve93.wm" "pCube1FollicleShape4285.spm";
connectAttr "hairSystemShape1.oh[46]" "pCube1FollicleShape4285.crp";
connectAttr "pCube1FollicleShape4291.ot" "pCube1Follicle4291.t" -l on;
connectAttr "pCube1FollicleShape4291.or" "pCube1Follicle4291.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4291.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4291.inm";
connectAttr "curveShape95.l" "pCube1FollicleShape4291.sp";
connectAttr "curve95.wm" "pCube1FollicleShape4291.spm";
connectAttr "hairSystemShape1.oh[47]" "pCube1FollicleShape4291.crp";
connectAttr "pCube1FollicleShape4296.ot" "pCube1Follicle4296.t" -l on;
connectAttr "pCube1FollicleShape4296.or" "pCube1Follicle4296.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4296.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4296.inm";
connectAttr "curveShape97.l" "pCube1FollicleShape4296.sp";
connectAttr "curve97.wm" "pCube1FollicleShape4296.spm";
connectAttr "hairSystemShape1.oh[48]" "pCube1FollicleShape4296.crp";
connectAttr "pCube1FollicleShape4702.ot" "pCube1Follicle4702.t" -l on;
connectAttr "pCube1FollicleShape4702.or" "pCube1Follicle4702.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4702.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4702.inm";
connectAttr "curveShape99.l" "pCube1FollicleShape4702.sp";
connectAttr "curve99.wm" "pCube1FollicleShape4702.spm";
connectAttr "hairSystemShape1.oh[49]" "pCube1FollicleShape4702.crp";
connectAttr "pCube1FollicleShape4707.ot" "pCube1Follicle4707.t" -l on;
connectAttr "pCube1FollicleShape4707.or" "pCube1Follicle4707.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4707.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4707.inm";
connectAttr "curveShape101.l" "pCube1FollicleShape4707.sp";
connectAttr "curve101.wm" "pCube1FollicleShape4707.spm";
connectAttr "hairSystemShape1.oh[50]" "pCube1FollicleShape4707.crp";
connectAttr "pCube1FollicleShape4712.ot" "pCube1Follicle4712.t" -l on;
connectAttr "pCube1FollicleShape4712.or" "pCube1Follicle4712.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4712.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4712.inm";
connectAttr "curveShape103.l" "pCube1FollicleShape4712.sp";
connectAttr "curve103.wm" "pCube1FollicleShape4712.spm";
connectAttr "hairSystemShape1.oh[51]" "pCube1FollicleShape4712.crp";
connectAttr "pCube1FollicleShape4717.ot" "pCube1Follicle4717.t" -l on;
connectAttr "pCube1FollicleShape4717.or" "pCube1Follicle4717.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4717.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4717.inm";
connectAttr "curveShape105.l" "pCube1FollicleShape4717.sp";
connectAttr "curve105.wm" "pCube1FollicleShape4717.spm";
connectAttr "hairSystemShape1.oh[52]" "pCube1FollicleShape4717.crp";
connectAttr "pCube1FollicleShape4722.ot" "pCube1Follicle4722.t" -l on;
connectAttr "pCube1FollicleShape4722.or" "pCube1Follicle4722.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4722.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4722.inm";
connectAttr "curveShape107.l" "pCube1FollicleShape4722.sp";
connectAttr "curve107.wm" "pCube1FollicleShape4722.spm";
connectAttr "hairSystemShape1.oh[53]" "pCube1FollicleShape4722.crp";
connectAttr "pCube1FollicleShape4727.ot" "pCube1Follicle4727.t" -l on;
connectAttr "pCube1FollicleShape4727.or" "pCube1Follicle4727.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4727.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4727.inm";
connectAttr "curveShape109.l" "pCube1FollicleShape4727.sp";
connectAttr "curve109.wm" "pCube1FollicleShape4727.spm";
connectAttr "hairSystemShape1.oh[54]" "pCube1FollicleShape4727.crp";
connectAttr "pCube1FollicleShape4732.ot" "pCube1Follicle4732.t" -l on;
connectAttr "pCube1FollicleShape4732.or" "pCube1Follicle4732.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4732.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4732.inm";
connectAttr "curveShape111.l" "pCube1FollicleShape4732.sp";
connectAttr "curve111.wm" "pCube1FollicleShape4732.spm";
connectAttr "hairSystemShape1.oh[55]" "pCube1FollicleShape4732.crp";
connectAttr "pCube1FollicleShape4737.ot" "pCube1Follicle4737.t" -l on;
connectAttr "pCube1FollicleShape4737.or" "pCube1Follicle4737.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4737.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4737.inm";
connectAttr "curveShape113.l" "pCube1FollicleShape4737.sp";
connectAttr "curve113.wm" "pCube1FollicleShape4737.spm";
connectAttr "hairSystemShape1.oh[56]" "pCube1FollicleShape4737.crp";
connectAttr "pCube1FollicleShape4742.ot" "pCube1Follicle4742.t" -l on;
connectAttr "pCube1FollicleShape4742.or" "pCube1Follicle4742.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4742.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4742.inm";
connectAttr "curveShape115.l" "pCube1FollicleShape4742.sp";
connectAttr "curve115.wm" "pCube1FollicleShape4742.spm";
connectAttr "hairSystemShape1.oh[57]" "pCube1FollicleShape4742.crp";
connectAttr "pCube1FollicleShape4747.ot" "pCube1Follicle4747.t" -l on;
connectAttr "pCube1FollicleShape4747.or" "pCube1Follicle4747.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4747.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4747.inm";
connectAttr "curveShape117.l" "pCube1FollicleShape4747.sp";
connectAttr "curve117.wm" "pCube1FollicleShape4747.spm";
connectAttr "hairSystemShape1.oh[58]" "pCube1FollicleShape4747.crp";
connectAttr "pCube1FollicleShape4752.ot" "pCube1Follicle4752.t" -l on;
connectAttr "pCube1FollicleShape4752.or" "pCube1Follicle4752.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4752.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4752.inm";
connectAttr "curveShape119.l" "pCube1FollicleShape4752.sp";
connectAttr "curve119.wm" "pCube1FollicleShape4752.spm";
connectAttr "hairSystemShape1.oh[59]" "pCube1FollicleShape4752.crp";
connectAttr "pCube1FollicleShape4757.ot" "pCube1Follicle4757.t" -l on;
connectAttr "pCube1FollicleShape4757.or" "pCube1Follicle4757.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4757.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4757.inm";
connectAttr "curveShape121.l" "pCube1FollicleShape4757.sp";
connectAttr "curve121.wm" "pCube1FollicleShape4757.spm";
connectAttr "hairSystemShape1.oh[60]" "pCube1FollicleShape4757.crp";
connectAttr "pCube1FollicleShape4762.ot" "pCube1Follicle4762.t" -l on;
connectAttr "pCube1FollicleShape4762.or" "pCube1Follicle4762.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4762.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4762.inm";
connectAttr "curveShape123.l" "pCube1FollicleShape4762.sp";
connectAttr "curve123.wm" "pCube1FollicleShape4762.spm";
connectAttr "hairSystemShape1.oh[61]" "pCube1FollicleShape4762.crp";
connectAttr "pCube1FollicleShape4767.ot" "pCube1Follicle4767.t" -l on;
connectAttr "pCube1FollicleShape4767.or" "pCube1Follicle4767.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4767.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4767.inm";
connectAttr "curveShape125.l" "pCube1FollicleShape4767.sp";
connectAttr "curve125.wm" "pCube1FollicleShape4767.spm";
connectAttr "hairSystemShape1.oh[62]" "pCube1FollicleShape4767.crp";
connectAttr "pCube1FollicleShape4772.ot" "pCube1Follicle4772.t" -l on;
connectAttr "pCube1FollicleShape4772.or" "pCube1Follicle4772.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4772.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4772.inm";
connectAttr "curveShape127.l" "pCube1FollicleShape4772.sp";
connectAttr "curve127.wm" "pCube1FollicleShape4772.spm";
connectAttr "hairSystemShape1.oh[63]" "pCube1FollicleShape4772.crp";
connectAttr "pCube1FollicleShape4777.ot" "pCube1Follicle4777.t" -l on;
connectAttr "pCube1FollicleShape4777.or" "pCube1Follicle4777.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4777.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4777.inm";
connectAttr "curveShape129.l" "pCube1FollicleShape4777.sp";
connectAttr "curve129.wm" "pCube1FollicleShape4777.spm";
connectAttr "hairSystemShape1.oh[64]" "pCube1FollicleShape4777.crp";
connectAttr "pCube1FollicleShape4782.ot" "pCube1Follicle4782.t" -l on;
connectAttr "pCube1FollicleShape4782.or" "pCube1Follicle4782.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4782.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4782.inm";
connectAttr "curveShape131.l" "pCube1FollicleShape4782.sp";
connectAttr "curve131.wm" "pCube1FollicleShape4782.spm";
connectAttr "hairSystemShape1.oh[65]" "pCube1FollicleShape4782.crp";
connectAttr "pCube1FollicleShape4787.ot" "pCube1Follicle4787.t" -l on;
connectAttr "pCube1FollicleShape4787.or" "pCube1Follicle4787.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4787.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4787.inm";
connectAttr "curveShape133.l" "pCube1FollicleShape4787.sp";
connectAttr "curve133.wm" "pCube1FollicleShape4787.spm";
connectAttr "hairSystemShape1.oh[66]" "pCube1FollicleShape4787.crp";
connectAttr "pCube1FollicleShape4792.ot" "pCube1Follicle4792.t" -l on;
connectAttr "pCube1FollicleShape4792.or" "pCube1Follicle4792.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4792.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4792.inm";
connectAttr "curveShape135.l" "pCube1FollicleShape4792.sp";
connectAttr "curve135.wm" "pCube1FollicleShape4792.spm";
connectAttr "hairSystemShape1.oh[67]" "pCube1FollicleShape4792.crp";
connectAttr "pCube1FollicleShape4797.ot" "pCube1Follicle4797.t" -l on;
connectAttr "pCube1FollicleShape4797.or" "pCube1Follicle4797.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape4797.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape4797.inm";
connectAttr "curveShape137.l" "pCube1FollicleShape4797.sp";
connectAttr "curve137.wm" "pCube1FollicleShape4797.spm";
connectAttr "hairSystemShape1.oh[68]" "pCube1FollicleShape4797.crp";
connectAttr "pCube1FollicleShape5202.ot" "pCube1Follicle5202.t" -l on;
connectAttr "pCube1FollicleShape5202.or" "pCube1Follicle5202.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5202.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5202.inm";
connectAttr "curveShape139.l" "pCube1FollicleShape5202.sp";
connectAttr "curve139.wm" "pCube1FollicleShape5202.spm";
connectAttr "hairSystemShape1.oh[69]" "pCube1FollicleShape5202.crp";
connectAttr "pCube1FollicleShape5207.ot" "pCube1Follicle5207.t" -l on;
connectAttr "pCube1FollicleShape5207.or" "pCube1Follicle5207.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5207.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5207.inm";
connectAttr "curveShape141.l" "pCube1FollicleShape5207.sp";
connectAttr "curve141.wm" "pCube1FollicleShape5207.spm";
connectAttr "hairSystemShape1.oh[70]" "pCube1FollicleShape5207.crp";
connectAttr "pCube1FollicleShape5212.ot" "pCube1Follicle5212.t" -l on;
connectAttr "pCube1FollicleShape5212.or" "pCube1Follicle5212.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5212.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5212.inm";
connectAttr "curveShape143.l" "pCube1FollicleShape5212.sp";
connectAttr "curve143.wm" "pCube1FollicleShape5212.spm";
connectAttr "hairSystemShape1.oh[71]" "pCube1FollicleShape5212.crp";
connectAttr "pCube1FollicleShape5217.ot" "pCube1Follicle5217.t" -l on;
connectAttr "pCube1FollicleShape5217.or" "pCube1Follicle5217.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5217.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5217.inm";
connectAttr "curveShape145.l" "pCube1FollicleShape5217.sp";
connectAttr "curve145.wm" "pCube1FollicleShape5217.spm";
connectAttr "hairSystemShape1.oh[72]" "pCube1FollicleShape5217.crp";
connectAttr "pCube1FollicleShape5222.ot" "pCube1Follicle5222.t" -l on;
connectAttr "pCube1FollicleShape5222.or" "pCube1Follicle5222.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5222.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5222.inm";
connectAttr "curveShape147.l" "pCube1FollicleShape5222.sp";
connectAttr "curve147.wm" "pCube1FollicleShape5222.spm";
connectAttr "hairSystemShape1.oh[73]" "pCube1FollicleShape5222.crp";
connectAttr "pCube1FollicleShape5227.ot" "pCube1Follicle5227.t" -l on;
connectAttr "pCube1FollicleShape5227.or" "pCube1Follicle5227.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5227.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5227.inm";
connectAttr "curveShape149.l" "pCube1FollicleShape5227.sp";
connectAttr "curve149.wm" "pCube1FollicleShape5227.spm";
connectAttr "hairSystemShape1.oh[74]" "pCube1FollicleShape5227.crp";
connectAttr "pCube1FollicleShape5232.ot" "pCube1Follicle5232.t" -l on;
connectAttr "pCube1FollicleShape5232.or" "pCube1Follicle5232.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5232.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5232.inm";
connectAttr "curveShape151.l" "pCube1FollicleShape5232.sp";
connectAttr "curve151.wm" "pCube1FollicleShape5232.spm";
connectAttr "hairSystemShape1.oh[75]" "pCube1FollicleShape5232.crp";
connectAttr "pCube1FollicleShape5237.ot" "pCube1Follicle5237.t" -l on;
connectAttr "pCube1FollicleShape5237.or" "pCube1Follicle5237.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5237.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5237.inm";
connectAttr "curveShape153.l" "pCube1FollicleShape5237.sp";
connectAttr "curve153.wm" "pCube1FollicleShape5237.spm";
connectAttr "hairSystemShape1.oh[76]" "pCube1FollicleShape5237.crp";
connectAttr "pCube1FollicleShape5242.ot" "pCube1Follicle5242.t" -l on;
connectAttr "pCube1FollicleShape5242.or" "pCube1Follicle5242.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5242.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5242.inm";
connectAttr "curveShape155.l" "pCube1FollicleShape5242.sp";
connectAttr "curve155.wm" "pCube1FollicleShape5242.spm";
connectAttr "hairSystemShape1.oh[77]" "pCube1FollicleShape5242.crp";
connectAttr "pCube1FollicleShape5247.ot" "pCube1Follicle5247.t" -l on;
connectAttr "pCube1FollicleShape5247.or" "pCube1Follicle5247.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5247.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5247.inm";
connectAttr "curveShape157.l" "pCube1FollicleShape5247.sp";
connectAttr "curve157.wm" "pCube1FollicleShape5247.spm";
connectAttr "hairSystemShape1.oh[78]" "pCube1FollicleShape5247.crp";
connectAttr "pCube1FollicleShape5252.ot" "pCube1Follicle5252.t" -l on;
connectAttr "pCube1FollicleShape5252.or" "pCube1Follicle5252.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5252.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5252.inm";
connectAttr "curveShape159.l" "pCube1FollicleShape5252.sp";
connectAttr "curve159.wm" "pCube1FollicleShape5252.spm";
connectAttr "hairSystemShape1.oh[79]" "pCube1FollicleShape5252.crp";
connectAttr "pCube1FollicleShape5257.ot" "pCube1Follicle5257.t" -l on;
connectAttr "pCube1FollicleShape5257.or" "pCube1Follicle5257.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5257.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5257.inm";
connectAttr "curveShape161.l" "pCube1FollicleShape5257.sp";
connectAttr "curve161.wm" "pCube1FollicleShape5257.spm";
connectAttr "hairSystemShape1.oh[80]" "pCube1FollicleShape5257.crp";
connectAttr "pCube1FollicleShape5262.ot" "pCube1Follicle5262.t" -l on;
connectAttr "pCube1FollicleShape5262.or" "pCube1Follicle5262.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5262.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5262.inm";
connectAttr "curveShape163.l" "pCube1FollicleShape5262.sp";
connectAttr "curve163.wm" "pCube1FollicleShape5262.spm";
connectAttr "hairSystemShape1.oh[81]" "pCube1FollicleShape5262.crp";
connectAttr "pCube1FollicleShape5267.ot" "pCube1Follicle5267.t" -l on;
connectAttr "pCube1FollicleShape5267.or" "pCube1Follicle5267.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5267.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5267.inm";
connectAttr "curveShape165.l" "pCube1FollicleShape5267.sp";
connectAttr "curve165.wm" "pCube1FollicleShape5267.spm";
connectAttr "hairSystemShape1.oh[82]" "pCube1FollicleShape5267.crp";
connectAttr "pCube1FollicleShape5272.ot" "pCube1Follicle5272.t" -l on;
connectAttr "pCube1FollicleShape5272.or" "pCube1Follicle5272.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5272.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5272.inm";
connectAttr "curveShape167.l" "pCube1FollicleShape5272.sp";
connectAttr "curve167.wm" "pCube1FollicleShape5272.spm";
connectAttr "hairSystemShape1.oh[83]" "pCube1FollicleShape5272.crp";
connectAttr "pCube1FollicleShape5277.ot" "pCube1Follicle5277.t" -l on;
connectAttr "pCube1FollicleShape5277.or" "pCube1Follicle5277.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5277.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5277.inm";
connectAttr "curveShape169.l" "pCube1FollicleShape5277.sp";
connectAttr "curve169.wm" "pCube1FollicleShape5277.spm";
connectAttr "hairSystemShape1.oh[84]" "pCube1FollicleShape5277.crp";
connectAttr "pCube1FollicleShape5282.ot" "pCube1Follicle5282.t" -l on;
connectAttr "pCube1FollicleShape5282.or" "pCube1Follicle5282.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5282.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5282.inm";
connectAttr "curveShape171.l" "pCube1FollicleShape5282.sp";
connectAttr "curve171.wm" "pCube1FollicleShape5282.spm";
connectAttr "hairSystemShape1.oh[85]" "pCube1FollicleShape5282.crp";
connectAttr "pCube1FollicleShape5287.ot" "pCube1Follicle5287.t" -l on;
connectAttr "pCube1FollicleShape5287.or" "pCube1Follicle5287.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5287.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5287.inm";
connectAttr "curveShape173.l" "pCube1FollicleShape5287.sp";
connectAttr "curve173.wm" "pCube1FollicleShape5287.spm";
connectAttr "hairSystemShape1.oh[86]" "pCube1FollicleShape5287.crp";
connectAttr "pCube1FollicleShape5292.ot" "pCube1Follicle5292.t" -l on;
connectAttr "pCube1FollicleShape5292.or" "pCube1Follicle5292.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5292.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5292.inm";
connectAttr "curveShape175.l" "pCube1FollicleShape5292.sp";
connectAttr "curve175.wm" "pCube1FollicleShape5292.spm";
connectAttr "hairSystemShape1.oh[87]" "pCube1FollicleShape5292.crp";
connectAttr "pCube1FollicleShape5297.ot" "pCube1Follicle5297.t" -l on;
connectAttr "pCube1FollicleShape5297.or" "pCube1Follicle5297.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5297.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5297.inm";
connectAttr "curveShape177.l" "pCube1FollicleShape5297.sp";
connectAttr "curve177.wm" "pCube1FollicleShape5297.spm";
connectAttr "hairSystemShape1.oh[88]" "pCube1FollicleShape5297.crp";
connectAttr "pCube1FollicleShape5703.ot" "pCube1Follicle5703.t" -l on;
connectAttr "pCube1FollicleShape5703.or" "pCube1Follicle5703.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5703.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5703.inm";
connectAttr "curveShape179.l" "pCube1FollicleShape5703.sp";
connectAttr "curve179.wm" "pCube1FollicleShape5703.spm";
connectAttr "hairSystemShape1.oh[89]" "pCube1FollicleShape5703.crp";
connectAttr "pCube1FollicleShape5708.ot" "pCube1Follicle5708.t" -l on;
connectAttr "pCube1FollicleShape5708.or" "pCube1Follicle5708.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5708.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5708.inm";
connectAttr "curveShape181.l" "pCube1FollicleShape5708.sp";
connectAttr "curve181.wm" "pCube1FollicleShape5708.spm";
connectAttr "hairSystemShape1.oh[90]" "pCube1FollicleShape5708.crp";
connectAttr "pCube1FollicleShape5714.ot" "pCube1Follicle5714.t" -l on;
connectAttr "pCube1FollicleShape5714.or" "pCube1Follicle5714.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5714.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5714.inm";
connectAttr "curveShape183.l" "pCube1FollicleShape5714.sp";
connectAttr "curve183.wm" "pCube1FollicleShape5714.spm";
connectAttr "hairSystemShape1.oh[91]" "pCube1FollicleShape5714.crp";
connectAttr "pCube1FollicleShape5719.ot" "pCube1Follicle5719.t" -l on;
connectAttr "pCube1FollicleShape5719.or" "pCube1Follicle5719.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5719.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5719.inm";
connectAttr "curveShape185.l" "pCube1FollicleShape5719.sp";
connectAttr "curve185.wm" "pCube1FollicleShape5719.spm";
connectAttr "hairSystemShape1.oh[92]" "pCube1FollicleShape5719.crp";
connectAttr "pCube1FollicleShape5725.ot" "pCube1Follicle5725.t" -l on;
connectAttr "pCube1FollicleShape5725.or" "pCube1Follicle5725.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5725.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5725.inm";
connectAttr "curveShape187.l" "pCube1FollicleShape5725.sp";
connectAttr "curve187.wm" "pCube1FollicleShape5725.spm";
connectAttr "hairSystemShape1.oh[93]" "pCube1FollicleShape5725.crp";
connectAttr "pCube1FollicleShape5730.ot" "pCube1Follicle5730.t" -l on;
connectAttr "pCube1FollicleShape5730.or" "pCube1Follicle5730.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5730.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5730.inm";
connectAttr "curveShape189.l" "pCube1FollicleShape5730.sp";
connectAttr "curve189.wm" "pCube1FollicleShape5730.spm";
connectAttr "hairSystemShape1.oh[94]" "pCube1FollicleShape5730.crp";
connectAttr "pCube1FollicleShape5736.ot" "pCube1Follicle5736.t" -l on;
connectAttr "pCube1FollicleShape5736.or" "pCube1Follicle5736.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5736.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5736.inm";
connectAttr "curveShape191.l" "pCube1FollicleShape5736.sp";
connectAttr "curve191.wm" "pCube1FollicleShape5736.spm";
connectAttr "hairSystemShape1.oh[95]" "pCube1FollicleShape5736.crp";
connectAttr "pCube1FollicleShape5741.ot" "pCube1Follicle5741.t" -l on;
connectAttr "pCube1FollicleShape5741.or" "pCube1Follicle5741.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5741.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5741.inm";
connectAttr "curveShape193.l" "pCube1FollicleShape5741.sp";
connectAttr "curve193.wm" "pCube1FollicleShape5741.spm";
connectAttr "hairSystemShape1.oh[96]" "pCube1FollicleShape5741.crp";
connectAttr "pCube1FollicleShape5747.ot" "pCube1Follicle5747.t" -l on;
connectAttr "pCube1FollicleShape5747.or" "pCube1Follicle5747.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5747.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5747.inm";
connectAttr "curveShape195.l" "pCube1FollicleShape5747.sp";
connectAttr "curve195.wm" "pCube1FollicleShape5747.spm";
connectAttr "hairSystemShape1.oh[97]" "pCube1FollicleShape5747.crp";
connectAttr "pCube1FollicleShape5752.ot" "pCube1Follicle5752.t" -l on;
connectAttr "pCube1FollicleShape5752.or" "pCube1Follicle5752.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5752.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5752.inm";
connectAttr "curveShape197.l" "pCube1FollicleShape5752.sp";
connectAttr "curve197.wm" "pCube1FollicleShape5752.spm";
connectAttr "hairSystemShape1.oh[98]" "pCube1FollicleShape5752.crp";
connectAttr "pCube1FollicleShape5758.ot" "pCube1Follicle5758.t" -l on;
connectAttr "pCube1FollicleShape5758.or" "pCube1Follicle5758.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5758.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5758.inm";
connectAttr "curveShape199.l" "pCube1FollicleShape5758.sp";
connectAttr "curve199.wm" "pCube1FollicleShape5758.spm";
connectAttr "hairSystemShape1.oh[99]" "pCube1FollicleShape5758.crp";
connectAttr "pCube1FollicleShape5763.ot" "pCube1Follicle5763.t" -l on;
connectAttr "pCube1FollicleShape5763.or" "pCube1Follicle5763.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5763.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5763.inm";
connectAttr "curveShape201.l" "pCube1FollicleShape5763.sp";
connectAttr "curve201.wm" "pCube1FollicleShape5763.spm";
connectAttr "hairSystemShape1.oh[100]" "pCube1FollicleShape5763.crp";
connectAttr "pCube1FollicleShape5769.ot" "pCube1Follicle5769.t" -l on;
connectAttr "pCube1FollicleShape5769.or" "pCube1Follicle5769.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5769.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5769.inm";
connectAttr "curveShape203.l" "pCube1FollicleShape5769.sp";
connectAttr "curve203.wm" "pCube1FollicleShape5769.spm";
connectAttr "hairSystemShape1.oh[101]" "pCube1FollicleShape5769.crp";
connectAttr "pCube1FollicleShape5774.ot" "pCube1Follicle5774.t" -l on;
connectAttr "pCube1FollicleShape5774.or" "pCube1Follicle5774.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5774.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5774.inm";
connectAttr "curveShape205.l" "pCube1FollicleShape5774.sp";
connectAttr "curve205.wm" "pCube1FollicleShape5774.spm";
connectAttr "hairSystemShape1.oh[102]" "pCube1FollicleShape5774.crp";
connectAttr "pCube1FollicleShape5780.ot" "pCube1Follicle5780.t" -l on;
connectAttr "pCube1FollicleShape5780.or" "pCube1Follicle5780.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5780.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5780.inm";
connectAttr "curveShape207.l" "pCube1FollicleShape5780.sp";
connectAttr "curve207.wm" "pCube1FollicleShape5780.spm";
connectAttr "hairSystemShape1.oh[103]" "pCube1FollicleShape5780.crp";
connectAttr "pCube1FollicleShape5785.ot" "pCube1Follicle5785.t" -l on;
connectAttr "pCube1FollicleShape5785.or" "pCube1Follicle5785.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5785.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5785.inm";
connectAttr "curveShape209.l" "pCube1FollicleShape5785.sp";
connectAttr "curve209.wm" "pCube1FollicleShape5785.spm";
connectAttr "hairSystemShape1.oh[104]" "pCube1FollicleShape5785.crp";
connectAttr "pCube1FollicleShape5791.ot" "pCube1Follicle5791.t" -l on;
connectAttr "pCube1FollicleShape5791.or" "pCube1Follicle5791.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5791.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5791.inm";
connectAttr "curveShape211.l" "pCube1FollicleShape5791.sp";
connectAttr "curve211.wm" "pCube1FollicleShape5791.spm";
connectAttr "hairSystemShape1.oh[105]" "pCube1FollicleShape5791.crp";
connectAttr "pCube1FollicleShape5796.ot" "pCube1Follicle5796.t" -l on;
connectAttr "pCube1FollicleShape5796.or" "pCube1Follicle5796.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape5796.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape5796.inm";
connectAttr "curveShape213.l" "pCube1FollicleShape5796.sp";
connectAttr "curve213.wm" "pCube1FollicleShape5796.spm";
connectAttr "hairSystemShape1.oh[106]" "pCube1FollicleShape5796.crp";
connectAttr "pCube1FollicleShape6203.ot" "pCube1Follicle6203.t" -l on;
connectAttr "pCube1FollicleShape6203.or" "pCube1Follicle6203.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6203.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6203.inm";
connectAttr "curveShape215.l" "pCube1FollicleShape6203.sp";
connectAttr "curve215.wm" "pCube1FollicleShape6203.spm";
connectAttr "hairSystemShape1.oh[107]" "pCube1FollicleShape6203.crp";
connectAttr "pCube1FollicleShape6209.ot" "pCube1Follicle6209.t" -l on;
connectAttr "pCube1FollicleShape6209.or" "pCube1Follicle6209.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6209.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6209.inm";
connectAttr "curveShape217.l" "pCube1FollicleShape6209.sp";
connectAttr "curve217.wm" "pCube1FollicleShape6209.spm";
connectAttr "hairSystemShape1.oh[108]" "pCube1FollicleShape6209.crp";
connectAttr "pCube1FollicleShape6215.ot" "pCube1Follicle6215.t" -l on;
connectAttr "pCube1FollicleShape6215.or" "pCube1Follicle6215.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6215.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6215.inm";
connectAttr "curveShape219.l" "pCube1FollicleShape6215.sp";
connectAttr "curve219.wm" "pCube1FollicleShape6215.spm";
connectAttr "hairSystemShape1.oh[109]" "pCube1FollicleShape6215.crp";
connectAttr "pCube1FollicleShape6222.ot" "pCube1Follicle6222.t" -l on;
connectAttr "pCube1FollicleShape6222.or" "pCube1Follicle6222.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6222.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6222.inm";
connectAttr "curveShape221.l" "pCube1FollicleShape6222.sp";
connectAttr "curve221.wm" "pCube1FollicleShape6222.spm";
connectAttr "hairSystemShape1.oh[110]" "pCube1FollicleShape6222.crp";
connectAttr "pCube1FollicleShape6228.ot" "pCube1Follicle6228.t" -l on;
connectAttr "pCube1FollicleShape6228.or" "pCube1Follicle6228.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6228.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6228.inm";
connectAttr "curveShape223.l" "pCube1FollicleShape6228.sp";
connectAttr "curve223.wm" "pCube1FollicleShape6228.spm";
connectAttr "hairSystemShape1.oh[111]" "pCube1FollicleShape6228.crp";
connectAttr "pCube1FollicleShape6234.ot" "pCube1Follicle6234.t" -l on;
connectAttr "pCube1FollicleShape6234.or" "pCube1Follicle6234.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6234.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6234.inm";
connectAttr "curveShape225.l" "pCube1FollicleShape6234.sp";
connectAttr "curve225.wm" "pCube1FollicleShape6234.spm";
connectAttr "hairSystemShape1.oh[112]" "pCube1FollicleShape6234.crp";
connectAttr "pCube1FollicleShape6240.ot" "pCube1Follicle6240.t" -l on;
connectAttr "pCube1FollicleShape6240.or" "pCube1Follicle6240.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6240.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6240.inm";
connectAttr "curveShape227.l" "pCube1FollicleShape6240.sp";
connectAttr "curve227.wm" "pCube1FollicleShape6240.spm";
connectAttr "hairSystemShape1.oh[113]" "pCube1FollicleShape6240.crp";
connectAttr "pCube1FollicleShape6246.ot" "pCube1Follicle6246.t" -l on;
connectAttr "pCube1FollicleShape6246.or" "pCube1Follicle6246.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6246.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6246.inm";
connectAttr "curveShape229.l" "pCube1FollicleShape6246.sp";
connectAttr "curve229.wm" "pCube1FollicleShape6246.spm";
connectAttr "hairSystemShape1.oh[114]" "pCube1FollicleShape6246.crp";
connectAttr "pCube1FollicleShape6253.ot" "pCube1Follicle6253.t" -l on;
connectAttr "pCube1FollicleShape6253.or" "pCube1Follicle6253.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6253.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6253.inm";
connectAttr "curveShape231.l" "pCube1FollicleShape6253.sp";
connectAttr "curve231.wm" "pCube1FollicleShape6253.spm";
connectAttr "hairSystemShape1.oh[115]" "pCube1FollicleShape6253.crp";
connectAttr "pCube1FollicleShape6259.ot" "pCube1Follicle6259.t" -l on;
connectAttr "pCube1FollicleShape6259.or" "pCube1Follicle6259.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6259.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6259.inm";
connectAttr "curveShape233.l" "pCube1FollicleShape6259.sp";
connectAttr "curve233.wm" "pCube1FollicleShape6259.spm";
connectAttr "hairSystemShape1.oh[116]" "pCube1FollicleShape6259.crp";
connectAttr "pCube1FollicleShape6265.ot" "pCube1Follicle6265.t" -l on;
connectAttr "pCube1FollicleShape6265.or" "pCube1Follicle6265.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6265.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6265.inm";
connectAttr "curveShape235.l" "pCube1FollicleShape6265.sp";
connectAttr "curve235.wm" "pCube1FollicleShape6265.spm";
connectAttr "hairSystemShape1.oh[117]" "pCube1FollicleShape6265.crp";
connectAttr "pCube1FollicleShape6271.ot" "pCube1Follicle6271.t" -l on;
connectAttr "pCube1FollicleShape6271.or" "pCube1Follicle6271.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6271.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6271.inm";
connectAttr "curveShape237.l" "pCube1FollicleShape6271.sp";
connectAttr "curve237.wm" "pCube1FollicleShape6271.spm";
connectAttr "hairSystemShape1.oh[118]" "pCube1FollicleShape6271.crp";
connectAttr "pCube1FollicleShape6277.ot" "pCube1Follicle6277.t" -l on;
connectAttr "pCube1FollicleShape6277.or" "pCube1Follicle6277.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6277.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6277.inm";
connectAttr "curveShape239.l" "pCube1FollicleShape6277.sp";
connectAttr "curve239.wm" "pCube1FollicleShape6277.spm";
connectAttr "hairSystemShape1.oh[119]" "pCube1FollicleShape6277.crp";
connectAttr "pCube1FollicleShape6284.ot" "pCube1Follicle6284.t" -l on;
connectAttr "pCube1FollicleShape6284.or" "pCube1Follicle6284.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6284.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6284.inm";
connectAttr "curveShape241.l" "pCube1FollicleShape6284.sp";
connectAttr "curve241.wm" "pCube1FollicleShape6284.spm";
connectAttr "hairSystemShape1.oh[120]" "pCube1FollicleShape6284.crp";
connectAttr "pCube1FollicleShape6290.ot" "pCube1Follicle6290.t" -l on;
connectAttr "pCube1FollicleShape6290.or" "pCube1Follicle6290.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6290.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6290.inm";
connectAttr "curveShape243.l" "pCube1FollicleShape6290.sp";
connectAttr "curve243.wm" "pCube1FollicleShape6290.spm";
connectAttr "hairSystemShape1.oh[121]" "pCube1FollicleShape6290.crp";
connectAttr "pCube1FollicleShape6296.ot" "pCube1Follicle6296.t" -l on;
connectAttr "pCube1FollicleShape6296.or" "pCube1Follicle6296.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6296.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6296.inm";
connectAttr "curveShape245.l" "pCube1FollicleShape6296.sp";
connectAttr "curve245.wm" "pCube1FollicleShape6296.spm";
connectAttr "hairSystemShape1.oh[122]" "pCube1FollicleShape6296.crp";
connectAttr "pCube1FollicleShape6704.ot" "pCube1Follicle6704.t" -l on;
connectAttr "pCube1FollicleShape6704.or" "pCube1Follicle6704.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6704.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6704.inm";
connectAttr "curveShape247.l" "pCube1FollicleShape6704.sp";
connectAttr "curve247.wm" "pCube1FollicleShape6704.spm";
connectAttr "hairSystemShape1.oh[123]" "pCube1FollicleShape6704.crp";
connectAttr "pCube1FollicleShape6712.ot" "pCube1Follicle6712.t" -l on;
connectAttr "pCube1FollicleShape6712.or" "pCube1Follicle6712.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6712.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6712.inm";
connectAttr "curveShape249.l" "pCube1FollicleShape6712.sp";
connectAttr "curve249.wm" "pCube1FollicleShape6712.spm";
connectAttr "hairSystemShape1.oh[124]" "pCube1FollicleShape6712.crp";
connectAttr "pCube1FollicleShape6721.ot" "pCube1Follicle6721.t" -l on;
connectAttr "pCube1FollicleShape6721.or" "pCube1Follicle6721.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape6721.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape6721.inm";
connectAttr "curveShape251.l" "pCube1FollicleShape6721.sp";
connectAttr "curve251.wm" "pCube1FollicleShape6721.spm";
connectAttr "hairSystemShape1.oh[125]" "pCube1FollicleShape6721.crp";
connectAttr "pCube1FollicleShape7204.ot" "pCube1Follicle7204.t" -l on;
connectAttr "pCube1FollicleShape7204.or" "pCube1Follicle7204.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape7204.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape7204.inm";
connectAttr "curveShape253.l" "pCube1FollicleShape7204.sp";
connectAttr "curve253.wm" "pCube1FollicleShape7204.spm";
connectAttr "hairSystemShape1.oh[126]" "pCube1FollicleShape7204.crp";
connectAttr "pCube1FollicleShape7211.ot" "pCube1Follicle7211.t" -l on;
connectAttr "pCube1FollicleShape7211.or" "pCube1Follicle7211.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape7211.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape7211.inm";
connectAttr "curveShape255.l" "pCube1FollicleShape7211.sp";
connectAttr "curve255.wm" "pCube1FollicleShape7211.spm";
connectAttr "hairSystemShape1.oh[127]" "pCube1FollicleShape7211.crp";
connectAttr "pCube1FollicleShape7219.ot" "pCube1Follicle7219.t" -l on;
connectAttr "pCube1FollicleShape7219.or" "pCube1Follicle7219.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape7219.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape7219.inm";
connectAttr "curveShape257.l" "pCube1FollicleShape7219.sp";
connectAttr "curve257.wm" "pCube1FollicleShape7219.spm";
connectAttr "hairSystemShape1.oh[128]" "pCube1FollicleShape7219.crp";
connectAttr "pCube1FollicleShape7704.ot" "pCube1Follicle7704.t" -l on;
connectAttr "pCube1FollicleShape7704.or" "pCube1Follicle7704.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape7704.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape7704.inm";
connectAttr "curveShape259.l" "pCube1FollicleShape7704.sp";
connectAttr "curve259.wm" "pCube1FollicleShape7704.spm";
connectAttr "hairSystemShape1.oh[129]" "pCube1FollicleShape7704.crp";
connectAttr "pCube1FollicleShape7711.ot" "pCube1Follicle7711.t" -l on;
connectAttr "pCube1FollicleShape7711.or" "pCube1Follicle7711.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape7711.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape7711.inm";
connectAttr "curveShape261.l" "pCube1FollicleShape7711.sp";
connectAttr "curve261.wm" "pCube1FollicleShape7711.spm";
connectAttr "hairSystemShape1.oh[130]" "pCube1FollicleShape7711.crp";
connectAttr "pCube1FollicleShape7719.ot" "pCube1Follicle7719.t" -l on;
connectAttr "pCube1FollicleShape7719.or" "pCube1Follicle7719.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape7719.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape7719.inm";
connectAttr "curveShape263.l" "pCube1FollicleShape7719.sp";
connectAttr "curve263.wm" "pCube1FollicleShape7719.spm";
connectAttr "hairSystemShape1.oh[131]" "pCube1FollicleShape7719.crp";
connectAttr "pCube1FollicleShape8204.ot" "pCube1Follicle8204.t" -l on;
connectAttr "pCube1FollicleShape8204.or" "pCube1Follicle8204.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape8204.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape8204.inm";
connectAttr "curveShape265.l" "pCube1FollicleShape8204.sp";
connectAttr "curve265.wm" "pCube1FollicleShape8204.spm";
connectAttr "hairSystemShape1.oh[132]" "pCube1FollicleShape8204.crp";
connectAttr "pCube1FollicleShape8212.ot" "pCube1Follicle8212.t" -l on;
connectAttr "pCube1FollicleShape8212.or" "pCube1Follicle8212.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape8212.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape8212.inm";
connectAttr "curveShape267.l" "pCube1FollicleShape8212.sp";
connectAttr "curve267.wm" "pCube1FollicleShape8212.spm";
connectAttr "hairSystemShape1.oh[133]" "pCube1FollicleShape8212.crp";
connectAttr "pCube1FollicleShape8221.ot" "pCube1Follicle8221.t" -l on;
connectAttr "pCube1FollicleShape8221.or" "pCube1Follicle8221.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape8221.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape8221.inm";
connectAttr "curveShape269.l" "pCube1FollicleShape8221.sp";
connectAttr "curve269.wm" "pCube1FollicleShape8221.spm";
connectAttr "hairSystemShape1.oh[134]" "pCube1FollicleShape8221.crp";
connectAttr "pCube1FollicleShape8705.ot" "pCube1Follicle8705.t" -l on;
connectAttr "pCube1FollicleShape8705.or" "pCube1Follicle8705.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape8705.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape8705.inm";
connectAttr "curveShape271.l" "pCube1FollicleShape8705.sp";
connectAttr "curve271.wm" "pCube1FollicleShape8705.spm";
connectAttr "hairSystemShape1.oh[135]" "pCube1FollicleShape8705.crp";
connectAttr "pCube1FollicleShape8715.ot" "pCube1Follicle8715.t" -l on;
connectAttr "pCube1FollicleShape8715.or" "pCube1Follicle8715.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape8715.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape8715.inm";
connectAttr "curveShape273.l" "pCube1FollicleShape8715.sp";
connectAttr "curve273.wm" "pCube1FollicleShape8715.spm";
connectAttr "hairSystemShape1.oh[136]" "pCube1FollicleShape8715.crp";
connectAttr "pCube1FollicleShape8725.ot" "pCube1Follicle8725.t" -l on;
connectAttr "pCube1FollicleShape8725.or" "pCube1Follicle8725.r" -l on;
connectAttr "pCubeShape1.wm" "pCube1FollicleShape8725.iwm";
connectAttr "pCubeShape1.o" "pCube1FollicleShape8725.inm";
connectAttr "curveShape275.l" "pCube1FollicleShape8725.sp";
connectAttr "curve275.wm" "pCube1FollicleShape8725.spm";
connectAttr "hairSystemShape1.oh[137]" "pCube1FollicleShape8725.crp";
connectAttr "pCube1FollicleShape1205.ocr" "curveShape2.cr";
connectAttr "pCube1FollicleShape1215.ocr" "curveShape4.cr";
connectAttr "pCube1FollicleShape1225.ocr" "curveShape6.cr";
connectAttr "pCube1FollicleShape1704.ocr" "curveShape8.cr";
connectAttr "pCube1FollicleShape1712.ocr" "curveShape10.cr";
connectAttr "pCube1FollicleShape1721.ocr" "curveShape12.cr";
connectAttr "pCube1FollicleShape2204.ocr" "curveShape14.cr";
connectAttr "pCube1FollicleShape2211.ocr" "curveShape16.cr";
connectAttr "pCube1FollicleShape2219.ocr" "curveShape18.cr";
connectAttr "pCube1FollicleShape2704.ocr" "curveShape20.cr";
connectAttr "pCube1FollicleShape2711.ocr" "curveShape22.cr";
connectAttr "pCube1FollicleShape2719.ocr" "curveShape24.cr";
connectAttr "pCube1FollicleShape3204.ocr" "curveShape26.cr";
connectAttr "pCube1FollicleShape3212.ocr" "curveShape28.cr";
connectAttr "pCube1FollicleShape3221.ocr" "curveShape30.cr";
connectAttr "pCube1FollicleShape3703.ocr" "curveShape32.cr";
connectAttr "pCube1FollicleShape3709.ocr" "curveShape34.cr";
connectAttr "pCube1FollicleShape3715.ocr" "curveShape36.cr";
connectAttr "pCube1FollicleShape3722.ocr" "curveShape38.cr";
connectAttr "pCube1FollicleShape3728.ocr" "curveShape40.cr";
connectAttr "pCube1FollicleShape3734.ocr" "curveShape42.cr";
connectAttr "pCube1FollicleShape3740.ocr" "curveShape44.cr";
connectAttr "pCube1FollicleShape3746.ocr" "curveShape46.cr";
connectAttr "pCube1FollicleShape3753.ocr" "curveShape48.cr";
connectAttr "pCube1FollicleShape3759.ocr" "curveShape50.cr";
connectAttr "pCube1FollicleShape3765.ocr" "curveShape52.cr";
connectAttr "pCube1FollicleShape3771.ocr" "curveShape54.cr";
connectAttr "pCube1FollicleShape3777.ocr" "curveShape56.cr";
connectAttr "pCube1FollicleShape3784.ocr" "curveShape58.cr";
connectAttr "pCube1FollicleShape3790.ocr" "curveShape60.cr";
connectAttr "pCube1FollicleShape3796.ocr" "curveShape62.cr";
connectAttr "pCube1FollicleShape4203.ocr" "curveShape64.cr";
connectAttr "pCube1FollicleShape4208.ocr" "curveShape66.cr";
connectAttr "pCube1FollicleShape4214.ocr" "curveShape68.cr";
connectAttr "pCube1FollicleShape4219.ocr" "curveShape70.cr";
connectAttr "pCube1FollicleShape4225.ocr" "curveShape72.cr";
connectAttr "pCube1FollicleShape4230.ocr" "curveShape74.cr";
connectAttr "pCube1FollicleShape4236.ocr" "curveShape76.cr";
connectAttr "pCube1FollicleShape4241.ocr" "curveShape78.cr";
connectAttr "pCube1FollicleShape4247.ocr" "curveShape80.cr";
connectAttr "pCube1FollicleShape4252.ocr" "curveShape82.cr";
connectAttr "pCube1FollicleShape4258.ocr" "curveShape84.cr";
connectAttr "pCube1FollicleShape4263.ocr" "curveShape86.cr";
connectAttr "pCube1FollicleShape4269.ocr" "curveShape88.cr";
connectAttr "pCube1FollicleShape4274.ocr" "curveShape90.cr";
connectAttr "pCube1FollicleShape4280.ocr" "curveShape92.cr";
connectAttr "pCube1FollicleShape4285.ocr" "curveShape94.cr";
connectAttr "pCube1FollicleShape4291.ocr" "curveShape96.cr";
connectAttr "pCube1FollicleShape4296.ocr" "curveShape98.cr";
connectAttr "pCube1FollicleShape4702.ocr" "curveShape100.cr";
connectAttr "pCube1FollicleShape4707.ocr" "curveShape102.cr";
connectAttr "pCube1FollicleShape4712.ocr" "curveShape104.cr";
connectAttr "pCube1FollicleShape4717.ocr" "curveShape106.cr";
connectAttr "pCube1FollicleShape4722.ocr" "curveShape108.cr";
connectAttr "pCube1FollicleShape4727.ocr" "curveShape110.cr";
connectAttr "pCube1FollicleShape4732.ocr" "curveShape112.cr";
connectAttr "pCube1FollicleShape4737.ocr" "curveShape114.cr";
connectAttr "pCube1FollicleShape4742.ocr" "curveShape116.cr";
connectAttr "pCube1FollicleShape4747.ocr" "curveShape118.cr";
connectAttr "pCube1FollicleShape4752.ocr" "curveShape120.cr";
connectAttr "pCube1FollicleShape4757.ocr" "curveShape122.cr";
connectAttr "pCube1FollicleShape4762.ocr" "curveShape124.cr";
connectAttr "pCube1FollicleShape4767.ocr" "curveShape126.cr";
connectAttr "pCube1FollicleShape4772.ocr" "curveShape128.cr";
connectAttr "pCube1FollicleShape4777.ocr" "curveShape130.cr";
connectAttr "pCube1FollicleShape4782.ocr" "curveShape132.cr";
connectAttr "pCube1FollicleShape4787.ocr" "curveShape134.cr";
connectAttr "pCube1FollicleShape4792.ocr" "curveShape136.cr";
connectAttr "pCube1FollicleShape4797.ocr" "curveShape138.cr";
connectAttr "pCube1FollicleShape5202.ocr" "curveShape140.cr";
connectAttr "pCube1FollicleShape5207.ocr" "curveShape142.cr";
connectAttr "pCube1FollicleShape5212.ocr" "curveShape144.cr";
connectAttr "pCube1FollicleShape5217.ocr" "curveShape146.cr";
connectAttr "pCube1FollicleShape5222.ocr" "curveShape148.cr";
connectAttr "pCube1FollicleShape5227.ocr" "curveShape150.cr";
connectAttr "pCube1FollicleShape5232.ocr" "curveShape152.cr";
connectAttr "pCube1FollicleShape5237.ocr" "curveShape154.cr";
connectAttr "pCube1FollicleShape5242.ocr" "curveShape156.cr";
connectAttr "pCube1FollicleShape5247.ocr" "curveShape158.cr";
connectAttr "pCube1FollicleShape5252.ocr" "curveShape160.cr";
connectAttr "pCube1FollicleShape5257.ocr" "curveShape162.cr";
connectAttr "pCube1FollicleShape5262.ocr" "curveShape164.cr";
connectAttr "pCube1FollicleShape5267.ocr" "curveShape166.cr";
connectAttr "pCube1FollicleShape5272.ocr" "curveShape168.cr";
connectAttr "pCube1FollicleShape5277.ocr" "curveShape170.cr";
connectAttr "pCube1FollicleShape5282.ocr" "curveShape172.cr";
connectAttr "pCube1FollicleShape5287.ocr" "curveShape174.cr";
connectAttr "pCube1FollicleShape5292.ocr" "curveShape176.cr";
connectAttr "pCube1FollicleShape5297.ocr" "curveShape178.cr";
connectAttr "pCube1FollicleShape5703.ocr" "curveShape180.cr";
connectAttr "pCube1FollicleShape5708.ocr" "curveShape182.cr";
connectAttr "pCube1FollicleShape5714.ocr" "curveShape184.cr";
connectAttr "pCube1FollicleShape5719.ocr" "curveShape186.cr";
connectAttr "pCube1FollicleShape5725.ocr" "curveShape188.cr";
connectAttr "pCube1FollicleShape5730.ocr" "curveShape190.cr";
connectAttr "pCube1FollicleShape5736.ocr" "curveShape192.cr";
connectAttr "pCube1FollicleShape5741.ocr" "curveShape194.cr";
connectAttr "pCube1FollicleShape5747.ocr" "curveShape196.cr";
connectAttr "pCube1FollicleShape5752.ocr" "curveShape198.cr";
connectAttr "pCube1FollicleShape5758.ocr" "curveShape200.cr";
connectAttr "pCube1FollicleShape5763.ocr" "curveShape202.cr";
connectAttr "pCube1FollicleShape5769.ocr" "curveShape204.cr";
connectAttr "pCube1FollicleShape5774.ocr" "curveShape206.cr";
connectAttr "pCube1FollicleShape5780.ocr" "curveShape208.cr";
connectAttr "pCube1FollicleShape5785.ocr" "curveShape210.cr";
connectAttr "pCube1FollicleShape5791.ocr" "curveShape212.cr";
connectAttr "pCube1FollicleShape5796.ocr" "curveShape214.cr";
connectAttr "pCube1FollicleShape6203.ocr" "curveShape216.cr";
connectAttr "pCube1FollicleShape6209.ocr" "curveShape218.cr";
connectAttr "pCube1FollicleShape6215.ocr" "curveShape220.cr";
connectAttr "pCube1FollicleShape6222.ocr" "curveShape222.cr";
connectAttr "pCube1FollicleShape6228.ocr" "curveShape224.cr";
connectAttr "pCube1FollicleShape6234.ocr" "curveShape226.cr";
connectAttr "pCube1FollicleShape6240.ocr" "curveShape228.cr";
connectAttr "pCube1FollicleShape6246.ocr" "curveShape230.cr";
connectAttr "pCube1FollicleShape6253.ocr" "curveShape232.cr";
connectAttr "pCube1FollicleShape6259.ocr" "curveShape234.cr";
connectAttr "pCube1FollicleShape6265.ocr" "curveShape236.cr";
connectAttr "pCube1FollicleShape6271.ocr" "curveShape238.cr";
connectAttr "pCube1FollicleShape6277.ocr" "curveShape240.cr";
connectAttr "pCube1FollicleShape6284.ocr" "curveShape242.cr";
connectAttr "pCube1FollicleShape6290.ocr" "curveShape244.cr";
connectAttr "pCube1FollicleShape6296.ocr" "curveShape246.cr";
connectAttr "pCube1FollicleShape6704.ocr" "curveShape248.cr";
connectAttr "pCube1FollicleShape6712.ocr" "curveShape250.cr";
connectAttr "pCube1FollicleShape6721.ocr" "curveShape252.cr";
connectAttr "pCube1FollicleShape7204.ocr" "curveShape254.cr";
connectAttr "pCube1FollicleShape7211.ocr" "curveShape256.cr";
connectAttr "pCube1FollicleShape7219.ocr" "curveShape258.cr";
connectAttr "pCube1FollicleShape7704.ocr" "curveShape260.cr";
connectAttr "pCube1FollicleShape7711.ocr" "curveShape262.cr";
connectAttr "pCube1FollicleShape7719.ocr" "curveShape264.cr";
connectAttr "pCube1FollicleShape8204.ocr" "curveShape266.cr";
connectAttr "pCube1FollicleShape8212.ocr" "curveShape268.cr";
connectAttr "pCube1FollicleShape8221.ocr" "curveShape270.cr";
connectAttr "pCube1FollicleShape8705.ocr" "curveShape272.cr";
connectAttr "pCube1FollicleShape8715.ocr" "curveShape274.cr";
connectAttr "pCube1FollicleShape8725.ocr" "curveShape276.cr";
connectAttr "hairSystemShape1.orh" "pfxHairShape1.rhs";
connectAttr ":time1.o" "nucleus1.cti";
connectAttr "hairSystemShape1.cust" "nucleus1.niao[0]";
connectAttr "hairSystemShape1.stst" "nucleus1.nias[0]";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "redshiftArchitectural1SG.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" "redshiftHair1SG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "redshiftArchitectural1SG.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" "redshiftHair1SG.message" ":defaultLightSet.message";
connectAttr ":mentalrayGlobals.msg" ":mentalrayItemsList.glb";
connectAttr ":miDefaultOptions.msg" ":mentalrayItemsList.opt" -na;
connectAttr ":miDefaultFramebuffer.msg" ":mentalrayItemsList.fb" -na;
connectAttr ":miDefaultOptions.msg" ":mentalrayGlobals.opt";
connectAttr ":miDefaultFramebuffer.msg" ":mentalrayGlobals.fb";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "polySurfaceShape1.o" "polySmoothFace1.ip";
connectAttr "redshiftArchitectural1.oc" "redshiftArchitectural1SG.ss";
connectAttr "pCubeShape1.iog" "redshiftArchitectural1SG.dsm" -na;
connectAttr "redshiftArchitectural1SG.msg" "materialInfo1.sg";
connectAttr "redshiftArchitectural1.msg" "materialInfo1.m";
connectAttr "redshiftArchitectural1.msg" "materialInfo1.t" -na;
connectAttr "redshiftHair1.oc" "redshiftHair1SG.ss";
connectAttr "redshiftHair1SG.msg" "materialInfo2.sg";
connectAttr "redshiftHair1.msg" "materialInfo2.m";
connectAttr "redshiftHair1.msg" "materialInfo2.t" -na;
connectAttr "redshiftArchitectural1SG.pa" ":renderPartition.st" -na;
connectAttr "redshiftHair1SG.pa" ":renderPartition.st" -na;
connectAttr "redshiftArchitectural1.msg" ":defaultShaderList1.s" -na;
connectAttr "redshiftHair1.msg" ":defaultShaderList1.s" -na;
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
connectAttr "redshiftDomeLightShape1.ltd" ":lightList1.l" -na;
connectAttr ":perspShape.msg" ":defaultRenderGlobals.sc";
connectAttr "redshiftDomeLight1.iog" ":defaultLightSet.dsm" -na;
// End of nhair.ma
