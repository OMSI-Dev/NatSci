using OpenCvSharp.Demo;
using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using OpenCvSharp;
using System.Xml.Serialization;
using System;
using ARSandbox;
using ARSandbox.WaterSimulation;
using UnityEngine.EventSystems;
using UnityEngine.Windows;
using UnityEditor;

public class CircleTracker : WebCamera
{
    //[SerializeField] private FlipMode ImageFlip;
    [SerializeField] private float Threshold = 240f;
    [SerializeField] private bool ShowProcessedImage = true;
    //[SerializeField] private float CurveAccuracy = 10.0f;
    //[SerializeField] private float MinArea = 5000f;

    public Slider thresholdSlider;
    public HandInput _HandInput;
    public GameObject BoundingCanvas;

    public GameObject rain;
    public ARSandbox.WaterSimulation.WaterSimulation _WaterSimulation;
    public ARSandbox.UI_SandboxHandInput _UIHandInput;
    public ARSandbox.CalibrationManager _calibrationManager;

    public GameObject whiteCircle;
    private Camera cam;

    private Mat image;
    private Mat processImage = new Mat();

    private CircleSegment[] circles;
    private CircleSegment chosen = new CircleSegment();
    private CircleSegment prevCircle = new CircleSegment();

    private double param1 = 100;
    private double param2 = 75;
    private int minRadius = 44;
    private int maxRadius = 60;
    private bool sliderShow = false;

    private Vector2 newRainPos = new Vector2();

    private Point2f boundingCenter = new Point2f();
    private float boundingRadius = new float();
    private CircleSegment boundingCircle = new CircleSegment();

    // Coordinates for the bounding box
    private float upperBoundX; // = 1300f;
    private float upperBoundY; // = 1000f;
    private float lowerBoundX; // = 600f;
    private float lowerBoundY; // = 300f;

    // Coordinates for the bounding circle
    private float boundingCircleCenterX;
    private float boundingCircleCenterY;
    private float boundingCircleRadiusX;
    private float boundingCircleRadiusY;

    public void Start()
    {
        cam  = Camera.main;

        if (!sliderShow)
        {
            thresholdSlider.gameObject.SetActive(false);
        }
        thresholdSlider.value = PlayerPrefs.GetFloat("CircleThresholdSlider");
        Threshold = thresholdSlider.value;

        /*// Get the circle bounds and square bounds
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
        upperBoundY = squareBounds.max.y; */
    }

    protected override bool ProcessTexture(WebCamTexture input, ref Texture2D output)
    {
        //Debug.Log("ProcessTexture called, input null: " + (input == null));

        /*if (BoundingCanvas.GetComponent<SphereTest>().EditingCircle())
        {
            // The circle is being edited if it's able to be grabbed.
            Vector3 circlePos = BoundingCanvas.GetComponent<SphereTest>().GetPosition();
            Vector3 circleScale = BoundingCanvas.GetComponent<SphereTest>().GetScale();
            boundingCircleCenterX = circlePos.x;
            boundingCircleCenterY = circlePos.y;
            boundingCircleRadiusX = circleScale.x;
            boundingCircleRadiusY = circleScale.y;

        }

        if (BoundingCanvas.GetComponent<SquareTest>().EditingSquare())
        {
            // The square is being edited if it's able to be grabbed.
            Bounds squareBounds = BoundingCanvas.GetComponent<SquareTest>().GetBounds();
            lowerBoundX = squareBounds.min.x;
            lowerBoundY = squareBounds.min.y;
            upperBoundX = squareBounds.max.x;
            upperBoundY = squareBounds.max.y;
        } */

        // Adjust the value of the threshold slider during the game and save when done
        if (UnityEngine.Input.GetKeyDown(KeyCode.Space))
        {
            if (!sliderShow)
            {
                sliderShow = true;
                thresholdSlider.gameObject.SetActive(true);
            }
            else
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

        /*boundingCenter.X = 9f;
        boundingCenter.Y = 10f;
        boundingRadius = 10f;

        boundingCircle.Radius = boundingRadius;
        boundingCircle.Center = boundingCenter; */

        image = OpenCvSharp.Unity.TextureToMat(input);

        // read and write to same image
        Cv2.Flip(image, image, FlipMode.X);
        Cv2.CvtColor(image, processImage, ColorConversionCodes.BGR2GRAY);
        //Cv2.Threshold(processImage, processImage, Threshold, 255, ThresholdTypes.BinaryInv);
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
                //if (WithinBounds(circle.Center.X, circle.Center.Y) || WithinCircularBounds(circle.Center.X, circle.Center.Y))
                //{
                    if (chosen.Radius == 0 || prevCircle.Radius != 0)
                    {
                        chosen = circle;
                    }

                // if the new circle detected isn't in the exact same 
                // position as the previous circle (ie it's not detecting
                // the same circle again), draw circle and move mouse to
                // center of the circle, then assign prevCircle to keep
                // track of the circle that was just drawn.
                //if (chosen.Center != prevCircle.Center && chosen.Radius != 0)
                if (chosen.Radius != 0)
                {

                    // X and Y are flipped - when making the point to create the rain, need to have x as y and y as x
                    Cv2.Circle(processImage, chosen.Center, (int)chosen.Radius, new Scalar(255, 0, 0), 1);
                    //Debug.Log("Circle radius: " + chosen.Radius);
                    //Vector3 moveCircle = new Vector3(MapXCoordinate(chosen.Center.Y), MapYCoordinate(chosen.Center.X), 0);
                    //Vector3 circleToScreenPos = cam.ScreenToWorldPoint(new Vector3(chosen.Center.Y, chosen.Center.X, 0));
                    //circleToScreenPos.x = (chosen.Center.X / Screen.width) * circleToScreenPos.x;
                    //whiteCircle.transform.position = new Vector3(circleToScreenPos.x, circleToScreenPos.y, 0);
                    //Debug.Log("Circle center coordinates: "+ chosen.Center);
                    newRainPos.x = MapXCoordinate(chosen.Center.Y);
                    newRainPos.y = MapYCoordinate(chosen.Center.X);
                    whiteCircle.transform.position = new Vector3(newRainPos.x, newRainPos.y, 0);
                    StartCoroutine(SimulatePointerClick(newRainPos));

                    prevCircle = chosen;
                }
                //}
            }
        }

        if (UnityEngine.Input.GetMouseButtonDown(0))
        {
            Debug.Log("Position at mouse click: " + UnityEngine.Input.mousePosition);
        }

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

    private float MapXCoordinate(float num)
    {
        return ((num / 1920) * 900) + ((Screen.width / 3));
    }

    private float MapYCoordinate(float num)
    {
        return ((num / 1080) * 870) - (Screen.height / 3);
    }

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
        if ((Mathf.Pow((checkX - h), 2) / Mathf.Pow(rx, 2)) + (Mathf.Pow((checkY - k), 2) / Mathf.Pow(ry, 2)) <= 1)
        {
            return true;
        }

        return false;
    }
}
