export default function Page() {
  return (
    <div className="min-h-screen bg-[#010a13] text-[#f0e6d2] flex items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-8">
        {/* Logo */}
        <div className="flex justify-center">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#c89b3c] to-[#785a28] flex items-center justify-center">
            <svg
              className="w-14 h-14 text-[#010a13]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
          </div>
        </div>

        {/* Title */}
        <div>
          <h1 className="text-4xl font-bold text-[#c89b3c] mb-2">JungleGap.ai</h1>
          <p className="text-[#a09b8c] text-lg">Real-Time League of Legends Jungle Tracker</p>
        </div>

        {/* Warning Box */}
        <div className="bg-[#1e2328] border-2 border-[#c89b3c] rounded-lg p-6 text-left">
          <div className="flex items-start gap-4">
            <div className="text-[#c89b3c] text-2xl">⚠️</div>
            <div>
              <h2 className="text-[#c89b3c] font-semibold text-lg mb-2">Application Electron</h2>
              <p className="text-[#a09b8c] mb-4">
                Cette application ne peut pas fonctionner dans le navigateur. Elle necessite Electron pour creer un
                overlay transparent au-dessus de League of Legends.
              </p>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-[#1e2328] rounded-lg p-6 text-left space-y-4">
          <h3 className="text-[#c89b3c] font-semibold">Pour lancer l&apos;application:</h3>
          <ol className="list-decimal list-inside space-y-2 text-[#a09b8c]">
            <li>Telecharge le ZIP (3 points en haut a droite → Download ZIP)</li>
            <li>Ouvre le projet dans VSCode</li>
            <li>
              Execute <code className="bg-[#0a0e13] px-2 py-1 rounded text-[#c89b3c]">npm install</code>
            </li>
            <li>
              Execute{" "}
              <code className="bg-[#0a0e13] px-2 py-1 rounded text-[#c89b3c]">
                cd backend && pip install -r requirements.txt
              </code>
            </li>
            <li>
              Lance le backend:{" "}
              <code className="bg-[#0a0e13] px-2 py-1 rounded text-[#c89b3c]">python engine.py --mock</code>
            </li>
            <li>
              Lance l&apos;app:{" "}
              <code className="bg-[#0a0e13] px-2 py-1 rounded text-[#c89b3c]">npm run electron-dev</code>
            </li>
          </ol>
        </div>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-[#1e2328] rounded-lg p-4">
            <div className="text-2xl mb-2">🎯</div>
            <p className="text-sm text-[#a09b8c]">Detection YOLO</p>
          </div>
          <div className="bg-[#1e2328] rounded-lg p-4">
            <div className="text-2xl mb-2">⚡</div>
            <p className="text-sm text-[#a09b8c]">Temps reel</p>
          </div>
          <div className="bg-[#1e2328] rounded-lg p-4">
            <div className="text-2xl mb-2">🖥️</div>
            <p className="text-sm text-[#a09b8c]">Overlay transparent</p>
          </div>
        </div>
      </div>
    </div>
  )
}
