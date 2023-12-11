import controlP5.*;
import peasy.*;


ControlP5 cp5;
// PeasyCam cam;

float phiValue;
float thetaValue;
float distValue;
int N = 64;

Cliff cliff;

void setup() {
  size(1920, 1080, P3D);
  
  //cam = new PeasyCam(this, 100);
  //cam.setMinimumDistance(50);
  //cam.setMaximumDistance(1000);
  
  /*
  cp5 = new ControlP5(this);
  cp5.addSlider("phiValue")
    .setSize(150, 20)
    .setPosition(100, 50)
    .setRange(0, 360)
    .setDefaultValue(30);
  cp5.addSlider("thetaValue")
    .setSize(150, 20)
    .setPosition(100, 20)
    .setRange(0, 360)
    .setDefaultValue(0);
  cp5.addSlider("distValue")
    .setSize(150, 20)
    .setPosition(100, 80)
    .setRange(0, 600)
    .setDefaultValue(300);
  */
  
  distValue = height * 2;
  phiValue = 10;
  thetaValue = 0;

  
  // cp5.setAutoDraw(false);
    
  smooth(8);
  cliff = new Cliff();
}

PVector[] computeLightArray(
  PVector pos,
  int l,
  int n
) {
  PVector[] lights = new PVector[n * n];
  
  pushMatrix();
  // rotateX(radians(thetaValue));
  translate(pos.x, pos.y, 0);
  rotateY(radians(-phiValue));
  translate(0, 0, pos.z);

    
  float L = l / n;
  float LL = l / 2;
  for (int i=0; i < n; i = i+1) {
    for (int j=0; j < n; j = j+1) {
      float x = L*i + L/2 - LL;
      float y = L*j + L/2 - LL;
      lights[n * i + j] = new PVector(
        modelX(x,y,0),
        modelY(x,y,0),
        modelZ(x,y,0)           
      );
    }
  }
      
  popMatrix();
  
  return lights;
  
  /*
  for (int i=0; i < n; i = i+1) {
    for (int j=0; j < n; j = j+1) {
        PVector lg = lights[n * i + j];
        print(lg.x, lg.y, lg.z);
    }
  }
  */
}

PVector centerLights(
  int l, float z
) {  
  return new PVector(
    width / 2,
    (height) / 2,
    z
  );
}

float computeBrightness(
  PVector[] lights, // 3d pos
  PVector target
) {
  // 0,N-1,(N-1)*N,N^2-1
  
  float count = 0;

  // WARNING!
  // count += cliff.rayUnobstructed(lights[0], target);
  // count += cliff.rayUnobstructed(lights[N-1], target);
  // count += cliff.rayUnobstructed(lights[(N-1)*N], target);
  // count += cliff.rayUnobstructed(lights[N*N-1], target);
  // if (count == 4) 
  //  return 1.0;
  for (int i=0; i < N; ++i) {
    count += cliff.rayUnobstructed(lights[i], target);
  }
  if (count == N)
    return 1.0;
  
  for (int i=0; i < lights.length; i++) {

    if (i % N == 0) 
      continue;
    count += cliff.rayUnobstructed(lights[i], target);
  }
  return count / lights.length;
}

void drawPlanes(
  int l, int n,
  color baseColor,
  color plateauColor
) {
  PVector[] lights = computeLightArray(centerLights(l, distValue), l, n);
  
  print(frameRate, '\n', lights[0].z);

  /*
  for (int y=0; y < height; ++y) {
    for (int x=0; x < width/2 + floor(profileOffset(y)) + 1; ++x) {
      // stroke(plateauColor);
      set(x,y, plateauColor);
    }
  }
  */
  
  fill(plateauColor);
  noStroke();
  beginShape();
  vertex(0,0);
  for (int i=0; i<height; i+=4) {
    vertex(cliff.cliff.get(1 + i/4).x, cliff.cliff.get(1 + i/4).y);
  }
  vertex(profileOffset(height) + width/2, height);
  vertex(0, height);
  endShape(CLOSE);
    
  for (int y=0; y <= height; ++y) {
    for (int x=width/2 + ceil(profileOffset(y)); x <= width; ++x) {
      float c = computeBrightness(lights, new PVector(x, y, 0));
      set(x,y, lerpColor(color(0), baseColor, c));
    }
  }
  
  cliff.draw(plateauColor);

  
  /*
  for (int i=0; i < n; i = i+1) {
    for (int j=0; j < n; j = j+1) {
        PVector lg = lights[n * i + j];
        // print(lg.x, lg.y, lg.z, ';');
        // strokeWeight(4);
        // stroke(255, 0, 0);
        point(lg.x,lg.y);
    }
  }
  */
}

void draw() {
  background(0);
  // test();
  // distValue = 400;
  // phiValue = 26.0;
  // distValue = 370.0;
  phiValue += 1;
  // thetaValue = (thetaValue += 2) % 7 - 3;
  
  drawPlanes(
    round(height*1.25), N, // below
    color(42, 61, 69),
    color(42, 61, 69)
    // color(22, 32, 36)
  );
  String s = str(int(random(100000)));
  save("curve" + s + ".jpg");
  
  // stroke(255);
  // strokeWeight(20);
  // point(0,0);
  
  //cam.beginHUD();
  //cp5.draw();
  //cam.endHUD();
}
