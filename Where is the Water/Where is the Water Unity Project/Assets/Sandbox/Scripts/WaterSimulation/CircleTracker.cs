using OpenCvSharp.Demo;
using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using OpenCvSharp;
using System.Xml.Serialization;
//using NUnit.Framework.Constraints;
//using Unity.VisualScripting;
using System;
using UnityEngine.InputSystem;
//using UnityEngine.UIElements;
using ARSandbox;
using ARSandbox.WaterSimulation;
using UnityEngine.EventSystems;
using UnityEngine.Windows;

public class CircleTracker : WebCamera
{
    [SerializeField] private FlipMode ImageFlip;
    [SerializeField] private float Threshold = 240f;
    [SerializeField] private bool ShowProcessedImage = true;
    [SerializeField] private float CurveAccuracy = 10.0f;
    [SerializeField] private float MinArea = 5000f;

    public Slider thresholdSlider;
    public HandInput _HandInput;
    public GameObject BoundingCanvas;

    public GameObject rain;
    public ARSandbox.WaterSimulation.WaterSimulation _WaterSimulation;
    public ARSandbox.UI_SandboxHandInput _UIHandInput;

    private Mat image;
    private Mat processImage = new Mat();

    private Point[][] contours;
    private HierarchyIndex[] hierarchy;

    private CircleSegment[] circles;
    private CircleSegment chosen = new CircleSegment();
    private CircleSegment prevCircle = new CircleSegment();

    private double param1 = 100;
    private double param2 = 50;
    private int minRadius = 25;
    private int maxRadius = 75;
    private bool sliderShow = false;

    private Vector2 newMousePos = new Vector2();

    private Point2f boundingCenter = new Point2f();
    private float boundingRadius = new float();
    private CircleSegment boundingCircle = new CircleSegment();

    // Coordinates for the bounding box
    private float upperBoundX = 1300f;
    private float upperBoundY = 1000f;
    private float lowerBoundX = 600f;
    private float lowerBoundY = 300f;

    // Coordinates for the bounding circle
    private float boundingCircleCenterX = 0f;
    private float boundingCircleCenterY = 0f;
    private float boundingCircleRadiusX = 0f;
    private float boundingCircleRadiusY = 0f;

    private bool circleBeingEdited = false;
    private bool squareBeingEdited = false;

    public void Start()
    {
        if(!sliderShow)
        {
            thresholdSlider.gameObject.SetActive(false);
        }
        thresholdSlider.value = PlayerPrefs.GetFloat("CircleThresholdSlider");
        Threshold = thresholdSlider.value;

        // Get the circle bounds and square bounds
        Vector3 circlePos = BoundingCanvas.GetComponent<SphereTest>().GetPosition();
        Vector3 circleScale = BoundingCanvas.GetComponent<SphereTest>().GetScale();
        boundingCircleCenterX = circlePos.x;
        boundingCircleCenterY = circlePos.y;
        boundingCircleRadiusX = circleScale.x;
        boundingCircleRadiusY = circleScale.y;

        Bounds squareBounds = BoundingCanvas.GetComponent<SquareTest>().GetBounds();
        lowerBoundX = squareBounds.min.x;
        lowerBoundY = squareBounds.min.y;
        upperBoundX = squareBounds.max.x;
        upperBoundY = squareBounds.max.y;
    }

    protected override bool ProcessTexture(WebCamTexture input, ref Texture2D output)
    {
        circleBeingEdited = BoundingCanvas.GetComponent<SphereTest>().EditingCircle();
        squareBeingEdited = BoundingCanvas.GetComponent<SquareTest>().EditingSquare();

        // update bounding circle as it is edited
        if (circleBeingEdited)
        {
            Vector3 circlePos = BoundingCanvas.GetComponent<SphereTest>().GetPosition();
            Vector3 circleScale = BoundingCanvas.GetComponent<SphereTest>().GetScale();
            boundingCircleCenterX = circlePos.x;
            boundingCircleCenterY = circlePos.y;
            boundingCircleRadiusX = circleScale.x;
            boundingCircleRadiusY = circleScale.y;
        }

        // update bounding square as it is edited
        if (squareBeingEdited)
        {
            Bounds squareBounds = BoundingCanvas.GetComponent<SquareTest>().GetBounds();
            lowerBoundX = squareBounds.min.x;
            lowerBoundY = squareBounds.min.y;
            upperBoundX = squareBounds.max.x;
            upperBoundY = squareBounds.max.y;
        }

        // Adjust the value of the threshold slider during the game and save when done
        if (UnityEngine.Input.GetKeyDown(KeyCode.Space))
        {
            if(!sliderShow)
            {
                sliderShow = true;
                thresholdSlider.gameObject.SetActive(true);
            } else
            {
                Threshold = thresholdSlider.value;
                PlayerPrefs.SetFloat("CircleThresholdSlider", thresholdSlider.value);
                sliderShow = false;
                thresholdSlider.gameObject.SetActive(false);
            }
        }
        if (sliderShow)
        {
            thresholdSlider.onValueChanged.AddListener(delegate { SliderValueChanged(); });
        }

        if (_UIHandInput == null)
        {
            _UIHandInput = FindObjectOfType<UI_SandboxHandInput>();
        }

        boundingCenter.X = 9f;
        boundingCenter.Y = 10f;
        boundingRadius = 10f;

        boundingCircle.Radius = boundingRadius;
        boundingCircle.Center = boundingCenter;

        if (UnityEngine.Input.GetMouseButtonDown(0))
        {
            Debug.Log(Mouse.current.position.ReadValue());
        }

        image = OpenCvSharp.Unity.TextureToMat(input);

        // read and write to same image
        Cv2.Flip(image, image, ImageFlip);
        Cv2.CvtColor(image, processImage, ColorConversionCodes.BGR2GRAY);
        Cv2.Threshold(processImage, processImage, Threshold, 255, ThresholdTypes.BinaryInv);
        Cv2.MedianBlur(processImage, processImage, 5);

        circles = Cv2.HoughCircles(processImage, HoughMethods.Gradient, 1.2,
                    700, param1, param2, minRadius, maxRadius);

        if (circles != null)
        {
            chosen.Radius = 0;
            prevCircle.Radius = 0;

            foreach (CircleSegment circle in circles)
            {
                // check here if circle is within the boundaries
                // before we assign chosen to anything
                if (WithinBounds(circle.Center.X, circle.Center.Y))
                {
                    if (chosen.Radius == 0 || prevCircle.Radius != 0)
                    {
                        chosen = circle;
                    }

                    // if the new circle detected isn't in the exact same 
                    // position as the previous circle (ie it's not detecting
                    // the same circle again), draw circle and move mouse to
                    // center of the circle, then assign prevCircle to keep
                    // track of the circle that was just drawn.
                    if (chosen.Center != prevCircle.Center && chosen.Radius != 0)
                    {
                        Cv2.Circle(processImage, chosen.Center, (int)chosen.Radius, new Scalar(127, 127, 127), 1);
                        newMousePos.x = MapXCoordinate(chosen.Center.Y);
                        newMousePos.y = MapYCoordinate(chosen.Center.X);
                        //Mouse.current.WarpCursorPosition(newMousePos);
                        StartCoroutine(SimulatePointerClick(newMousePos));
                        //_HandInput.OnUITouchDown(7045, newMousePos);
                        //_WaterSimulation.CreateWaterFromCircle(mouseWorldPos);
                        //StartCoroutine(SimulateDragGesture(newMousePos));
                        //_HandInput.OnUITouchDown(7045, newMousePos);

                        //rain.SetActive(true);
                        prevCircle = chosen;
                        //_HandInput.OnUITouchUp(7045);
                    }
                } else
                {
                    //rain.SetActive(false);
                }
            }
        }

        //Cv2.FindContours(processImage, out contours, out hierarchy, RetrievalModes.Tree, ContourApproximationModes.ApproxSimple, null);

        //foreach (Point[] contour in contours)
        //{
        //    Point[] points = Cv2.ApproxPolyDP(contour, CurveAccuracy, true);
        //    var area = Cv2.ContourArea(contour);

        //    if (area > MinArea)
        //    {
        //        drawContour(processImage, new Scalar(127, 127, 127), 2, points);
        //    }
        //}

        //only doing once, if output is null
        //only once as it will take up too much memory
        //to do this every time, otherwise if output is
        //not null, override the object that already exists
        if (output == null)
        {
            // format for statement in ()
            // (if var is true ? then do var : else do var)
            output = OpenCvSharp.Unity.MatToTexture(ShowProcessedImage ? processImage : image);
        }
        else
        {
            OpenCvSharp.Unity.MatToTexture(ShowProcessedImage ? processImage : image, output);
        }
        return true;
    }

    public void SliderValueChanged()
    {
        Threshold = thresholdSlider.value;
    }

    private IEnumerator SimulatePointerClick(Vector2 pos)
    {
        yield return new WaitForSeconds(0.5f);

        var fakeEvent = new PointerEventData(EventSystem.current);
        fakeEvent.position = pos;
        fakeEvent.pointerId = 7045;

        // simulate click
        _UIHandInput.OnPointerDown(fakeEvent);
        yield return new WaitForSeconds(0.2f);
        _UIHandInput.OnPointerUp(fakeEvent);
    }

    /*IEnumerator SimulateDragGesture(Vector2 pos)
    {
        // TOUCH DOWN
        bool touchDown = _HandInput.OnUITouchDown(7045, pos);
        Debug.Log("TouchDown result: " + touchDown);

        // TOUCH MOVE
        bool touchMove = _HandInput.OnUITouchMove(7045, pos);
        Debug.Log("TouchMove result: " + touchMove);

        // TOUCH UP
        yield return new WaitForSeconds(0.05f);
        bool touchUp = _HandInput.OnUITouchUp(7045);
        Debug.Log("TouchUp result: " + touchUp);
    } */

    // This function takes the x coordinate from the Kinect camera's view and maps it to the
    // coresponding coordinate for the Unity gameplay. Flipping the X coordinate and Y coordinate's axis.
    private float MapXCoordinate(float num)
    {
        return (((Screen.width / 4 - 20) * (num - 1300)) / (630 - 1300)) + 20;
    }

    private float MapYCoordinate(float num)
    {
        return ((((Screen.height + 200) - 300) * (num - 1000)) / (300 - 1000)) + 300;
    }

    //private void drawContour(Mat Image, Scalar Color, int Thickness, Point[] Points)
    //{
    //    for (int i = 1; i < Points.Length; i++)
    //    {
    //        // Connect all the points
    //        Cv2.Line(Image, Points[i - 1], Points[i], Color, Thickness);
    //    }
    //    // Close the shape, connect first and last points
    //    Cv2.Line(Image, Points[Points.Length - 1], Points[0], Color, Thickness);
    //}

    private bool WithinBounds(float checkX, float checkY)
    {
        if (lowerBoundX < checkX && checkX < upperBoundX &&
            lowerBoundY < checkY && checkY < upperBoundY)
        {
            return true;
        }

        return false;
    }

    private bool WithinCircularBounds(float checkX, float checkY)
    {
        float h = boundingCircleCenterX;
        float k = boundingCircleCenterY;
        float rx = boundingCircleRadiusX;
        float ry = boundingCircleRadiusY;

        // equation for chekcing if a point lies within or right on the line (<=) of an ellipse.
        if ( (Mathf.Pow((checkX - h), 2) / Mathf.Pow(rx, 2)) + (Mathf.Pow((checkY - k), 2) / Mathf.Pow(ry, 2)) <= 1)
        {
            return true;
        }

        return false;
    }
}
