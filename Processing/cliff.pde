float profileOffset2(int y) {  
  // float yp = abs(y - height*0.5) / 20;
  // float ypp = pow(yp, 1.6);
  // print(y, ypp, '\n');

  float yp = y * 0.02;
  float ypp = pow(yp, 2.6) - 100;

  return ypp;
}

float q(float y) {
  float a = 1;
  return pow(y, 1/a) * height / pow(height, 1/a);
}

float profileOffset3(int y) { // circle
  float x = y; // q(y);
  float R = height / 2;
  // float m = (1 + x*x / (height*height)) * 1/2;
  return (R + 1 + sqrt(R*R - pow(x - R, 2))) * 0.67 - 600;
  // return x;
}

float profileOffset(int y) {
  float yp = height - y;
  float R = height * 1.0 / 2;
  float x = acos((R - yp) / R);
  // return -R*(x-sin(x)) * 0.35 + 150;
  // return y * (524.0 / 1012) - 400;
  return 0;
}

float profileHeight(int y) {
  float yp = (30.0) * (1 - pow((y - height / 2.0), 2) / pow(height / 2.0, 2));
  if (abs(y - height/2) < height * 0.4)
    return 100;
  return 0; // - yp;
}

class Cliff {
  ArrayList<PVector> cliff;
  
  Cliff() {
    cliff = new ArrayList<PVector>();
    generateCliff();
  }
  
  void generateCliff() {
    float m = profileOffset(1) - profileOffset(0);
    cliff.add(new PVector(profileOffset(0) + width/2 - 300*m, -300, profileHeight(-300)));
    for (int i=0; i < height; i+=4) {
      cliff.add(new PVector(
        width / 2 + profileOffset(i), i,
        profileHeight(i)
      ));
    }
    cliff.add(new PVector(
      profileOffset(height) + width/2, 
      height, profileHeight(height)
    ));
    cliff.add(new PVector(
      profileOffset(height) + width/2, 
      height+300, profileHeight(height+300)
    ));
  }
  
  void draw(color cliffColor) {
    strokeWeight(2);
    stroke(cliffColor);
    noFill();
    
    beginShape();
    curveVertex(cliff.get(1).x, cliff.get(1).y);
    curveVertex(cliff.get(1).x, cliff.get(1).y);
    for (int i=0; i < height; i+=4) {
        curveVertex(cliff.get(1 + i/4).x, cliff.get(1 + i/4).y); 
    }
    PVector last = cliff.get(cliff.size() - 2);
    curveVertex(last.x, last.y);
    curveVertex(last.x, last.y);
    endShape();
  }
  
  private float cross(PVector v, PVector w) {
    return v.x * w.y - v.y * w.x; 
  }
  
  private PVector rayUnobstructedHelper(
    PVector p, PVector pr,
    PVector q, PVector qs
  ) {
    PVector r = new PVector(pr.x - p.x, pr.y - p.y);
    PVector s = new PVector(qs.x - q.x, qs.y - q.y);
    float c = cross(r, s);
    
    return new PVector(
      ((q.x - p.x) * s.y - (q.y - p.y) * s.x) / c,  // lerp param p->pr
      ((q.x - p.x) * r.y - (q.y - p.y) * r.x) / c,  // lerp param q->qr
      c / (r.mag() * s.mag())
      // sin(theta), theta: angle between tanget of 
      // the curve and the line p->pr
    );
  }

  float rayUnobstructed(
    PVector p, PVector q 
  ) {   
    int i = 0;
    while(i < cliff.size() - 1) {
      PVector a = rayUnobstructedHelper(
        p, q, cliff.get(i), cliff.get(i+1)
      );

      float c1 = 50;
      // the greater the curvature of gamma, 
      // the lower this value must be
      float c2 = 0.8;
  
      if (0 <= a.x && a.x <= 1 
        && 0 <= a.y && a.y <= 1)
      {     
        float z1 = (q.z - p.z) * a.x + p.z;
        float z2 = (cliff.get(i+1).z - cliff.get(i).z) * a.y
          + cliff.get(i).z;  
        if (z1 > z2) {
          return 1;
        } else {
          return 0; 
        }
      } else if (a.y > c1) {
        float z = abs(round(a.y * c2) * a.z);
        // print(z, a[0].z, '\n');
        i += z;
      }
      i += 1;
    }
    return 1;
  }
}
