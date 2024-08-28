<?php
// Database configuration
$servername = "kazumi7884.co.uk";
$username = "Kazumi7884";
$password = "31pQ$@&$!H48";
$dbname = "kazumi7884_main";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Check if form data is complete
if (isset($_POST['name']) && isset($_POST['title']) && isset($_POST['blog']) && isset($_POST['destination'])) {
    $name = $_POST['name'];
    $title = $_POST['title'];
    $blog = $_POST['blog'];
    $destination = $_POST['destination']; // Destination page specified in the form

    // Insert data into the database
    $sql = "INSERT INTO blog_posts (name, title, blog) VALUES (?, ?, ?)";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("sss", $name, $title, $blog);
    if ($stmt->execute()) {
        echo "Blog post submitted successfully!";
    } else {
        echo "Error: " . $sql . "<br>" . $conn->error;
    }
    $stmt->close();
} else {
    echo "Form data is not complete.";
}

// Close connection
$conn->close();

// Redirect to the specified destination page
header("Location: $destination");
exit(); // Make sure to exit after sending the header
?>
