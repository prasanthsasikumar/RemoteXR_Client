# RemoteXR_Client

A Unity-based remote expert collaboration system that enables real-time multi-user experiences with spatial alignment and eye gaze tracking capabilities. This client allows remote users (desktop/laptop) to view and interact with VR users' environments through networked 3D representations.

## 🎯 Overview

RemoteXR_Client is the remote expert/desktop component of a collaborative XR system. It connects to VR users (MeshVR) through Photon networking, displaying their scanned environments and enabling real-time interaction and guidance.

### Key Features

- **Multi-User Networking**: Real-time synchronization using Photon PUN (Photon Unity Networking)
- **Spatial Alignment System**: Automatic coordinate system alignment between VR and desktop users
- **Mesh Visualization**: View and interact with 3D-scanned environments from VR users
- **Free-Fly Camera**: Navigate the remote environment with WASD + mouse controls
- **Eye Gaze Integration**: Receive and display eye tracking data via Lab Streaming Layer (LSL)
- **Interactive Mesh Alignment**: Tools for VR users to calibrate and align their scanned meshes
- **Player Representation**: Visual markers showing remote and local user positions
- **Debug UI**: Real-time networking and alignment status display

## 🏗️ Architecture

### Core Components

1. **RemoteClient.cs**
   - Handles remote user connection and free-fly camera controls
   - Manages Photon networking connection
   - Synchronizes remote user position/rotation with other clients
   - WASD + mouse look controls for desktop navigation

2. **NetworkedPlayer.cs**
   - Represents each player in the networked scene
   - Handles spatial coordinate transformation between VR and desktop users
   - Provides visual differentiation (blue for local, red for remote)
   - Displays player name tags

3. **SpatialAlignmentManager.cs**
   - Manages coordinate system alignment between different client types
   - Supports multiple alignment modes:
     - `AutoAlign`: Automatic mesh-based alignment
     - `ManualAlign`: Manual offset configuration
     - `MarkerBased`: Calibration using alignment markers
     - `SharedOrigin`: Same coordinate system (no alignment needed)
   - Synchronizes alignment data across all clients via RPC

4. **MeshAlignmentTool.cs**
   - Interactive tool for VR users to align scanned meshes with real-world geometry
   - Keyboard controls for position, rotation, and scale adjustments
   - Fine adjustment mode for precise calibration
   - Persistent alignment storage via PlayerPrefs
   - Network synchronization of alignment changes

5. **LslGazeReceiver.cs**
   - Receives real-time eye gaze data via Lab Streaming Layer (LSL)
   - Connects to external eye tracking systems (e.g., EyeTrax)
   - Processes 3-channel gaze data: [gaze_x, gaze_y, pupil_size]

6. **PhotonDebugUI.cs**
   - On-screen debug information for networking status
   - Displays connection state, room info, and player count

## 🚀 Getting Started

### Prerequisites

- **Unity 2021.3 LTS or newer** (tested with Unity 2021.3+)
- **Photon PUN 2** (included in project)
- **Lab Streaming Layer for Unity** (optional, for eye tracking)
- **A Photon account** (free tier available at [Photon Engine](https://www.photonengine.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/prasanthsasikumar/RemoteXR_Client.git
   cd RemoteXR_Client
   ```

2. **Open in Unity**
   - Launch Unity Hub
   - Click "Open" and select the `RemoteXR_Client` folder
   - Wait for Unity to import all assets

3. **Configure Photon**
   - Create a free account at [Photon Engine](https://www.photonengine.com/)
   - Create a new PUN application
   - In Unity: `Window > Photon Unity Networking > PUN Wizard`
   - Enter your Photon App ID
   - Set the region to your preferred server location

4. **Setup Required Prefabs**
   - Ensure `LocalClientCube` prefab exists in `Assets/Resources/` folder
   - Add `PhotonView` component to the prefab
   - Add `PhotonTransformView` component for position/rotation sync
   - Add `NetworkedPlayer` component
   - Configure PhotonView to observe the PhotonTransformView component

### Configuration

#### Room Settings
By default, clients connect to room: **"MeshVRRoom"**
- Maximum players: 4
- Auto-reconnect enabled

To change the room name, edit the `OnConnectedToMaster()` method in `RemoteClient.cs`:
```csharp
PhotonNetwork.JoinOrCreateRoom("YourRoomName", new RoomOptions { MaxPlayers = 4 }, TypedLobby.Default);
```

#### Alignment Configuration
Edit `SpatialAlignmentManager` settings in Unity Inspector:
- **Mesh Reference Point**: Transform representing the mesh's origin
- **Alignment Mode**: Choose from AutoAlign, ManualAlign, MarkerBased, or SharedOrigin
- **Show Debug Info**: Toggle on-screen alignment data display

## 🎮 Controls

### Remote Client (Desktop) - Free-Fly Camera

| Input | Action |
|-------|--------|
| `W` / `S` | Move forward / backward |
| `A` / `D` | Move left / right |
| `E` / `Q` | Move up / down |
| `Right Mouse Button` + Mouse Move | Look around |
| `Shift` (hold) | Increase movement speed (3x) |
| `Ctrl` (hold) | Decrease movement speed (0.3x) |

### Mesh Alignment Tool (VR Users)

| Input | Action |
|-------|--------|
| `M` | Toggle alignment mode on/off |
| `Numpad 8/2/4/6` or Arrow Keys | Move mesh (Forward/Back/Left/Right) |
| `Page Up` / `Page Down` | Move mesh up/down |
| `Numpad 9` / `Numpad 3` | Move mesh up/down (alternative) |
| `Ctrl` + Numpad | Rotate mesh |
| `+` / `-` | Scale mesh up/down |
| `F` | Toggle fine adjustment mode |
| `Enter` | Save current alignment |
| `Ctrl` + `R` | Reset to original position |
| `Ctrl` + `L` | Load saved alignment |
| `Esc` | Exit alignment mode |

## 📡 Eye Tracking Integration

### EyeTrax Setup

This project integrates with [EyeTrax](https://github.com/ck-zhang/EyeTrax) for eye gaze streaming via LSL.

1. **Install EyeTrax**
   ```bash
   git clone https://github.com/ck-zhang/eyetrax && cd eyetrax
   
   # editable install — pick one
   python -m pip install -e .
   # OR
   pip install uv && uv sync
   ```

2. **Configure LSL Receiver**
   - Add `LslGazeReceiver` component to a GameObject in your scene
   - Set **Stream Name**: "EyeGaze"
   - Set **Stream Type**: "Gaze"
   - Set **Channel Count**: 3 (x, y, pupil)

3. **Start Streaming**
   - Run your eye tracking Python script
   - Unity will automatically connect to the LSL stream
   - View gaze data in the Unity Console

## 🔧 Networking Architecture

### Photon PUN 2 Setup

**Important**: All networked prefabs MUST have:
1. `PhotonView` component
2. `PhotonTransformView` component (for position/rotation sync)
3. Be placed in `Assets/Resources/` folder
4. PhotonView must observe the PhotonTransformView

### Data Synchronization

- **Player Positions**: Synced via `PhotonTransformView` (automatic)
- **Mesh Alignment**: Synced via RPC calls in `MeshAlignmentTool`
- **Coordinate Transformation**: Managed by `SpatialAlignmentManager` RPC system

### Network Flow

```
RemoteClient (Desktop)                    VR Client (MeshVR)
       |                                         |
       |-- Connect to Photon Master ----------->|
       |                                         |
       |<- Join/Create "MeshVRRoom" ----------->|
       |                                         |
       |-- Spawn LocalClientCube prefab ------->|
       |<- See VR user's position/orientation --|
       |                                         |
       |<- Receive mesh alignment data ---------|
       |                                         |
       |-- Spatial alignment transform -------->|
       |<------- Real-time position sync ------>|
```

## 🐛 Troubleshooting

### Common Issues

**1. PhotonNetwork.Instantiate() error**
```
PhotonNetwork.Instantiate() can only instantiate objects with a PhotonView component
```
**Solution**: Add `PhotonView` component to your prefab in `Assets/Resources/`

**2. Players not visible**
- Ensure both clients are in the same Photon room
- Check that prefab is in `Resources` folder
- Verify PhotonView is properly configured

**3. Mesh misalignment**
- Enter alignment mode (`M` key)
- Manually adjust mesh position/rotation
- Save alignment (`Enter` key)
- Verify `SpatialAlignmentManager` is configured

**4. LSL connection fails**
- Check that EyeTrax or other LSL source is running
- Verify stream name matches ("EyeGaze")
- Check LSL library is properly imported

**5. Network lag/stuttering**
- Reduce `PhotonTransformView` send rate
- Check internet connection stability
- Consider changing Photon region in settings

## 📁 Project Structure

```
Assets/
├── RemoteClient.cs              # Main remote user controller
├── NetworkedPlayer.cs           # Player representation & sync
├── SpatialAlignmentManager.cs   # Coordinate system alignment
├── MeshAlignmentTool.cs         # Interactive mesh calibration
├── PhotonDebugUI.cs             # Debug overlay
├── AlignmentCalibrationTool.cs  # Calibration utilities
├── Resources/                   # Photon instantiable prefabs
│   └── LocalClientCube.prefab   # Player representation
├── Scenes/
│   ├── LslGazeReceiver.cs      # Eye tracking integration
│   └── [Scene files]
├── Photon/                      # Photon Unity Networking
└── Settings/                    # Unity project settings
```

## 🤝 Related Projects

This client works in conjunction with:
- **MeshVR** - The VR client component (HoloLens 2/Quest)
- **EyeTrax** - Eye tracking data streaming ([GitHub](https://github.com/ck-zhang/EyeTrax))

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Photon Unity Networking** by Exit Games
- **EyeTrax** by ck-zhang
- **Lab Streaming Layer** by SCCN

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [prasanthsasikumar](https://github.com/prasanthsasikumar)

---

**Status**: Active Development  
**Unity Version**: 2021.3 LTS+  
**Platform**: Windows / macOS (Desktop)