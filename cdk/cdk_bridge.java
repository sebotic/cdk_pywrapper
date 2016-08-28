import py4j.GatewayServer;
import org.openscience.cdk.*;

class CDKBridge {

  public static void main(String[] args) {
    CDKBridge app = new CDKBridge();
    GatewayServer server = new GatewayServer(app);
    server.start();
    System.out.println("Server process started sucessfully");
  }
}
