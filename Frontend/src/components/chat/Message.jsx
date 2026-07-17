import { motion } from "framer-motion";

export default function Message({

  role,

  avatar,

  children,

  citations

}) {

  const isUser = role === "user";


  return (

    <motion.div

      className={`msg-row ${isUser ? "user" : "assistant"}`}

      initial={{
        opacity: 0,
        x: isUser ? 20 : -20,
        y: 10
      }}

      animate={{
        opacity: 1,
        x: 0,
        y: 0
      }}

      transition={{
        duration: 0.25,
        ease: "easeOut"
      }}

    >

      <div
        className={`msg-avatar ${
          isUser
          ? "user-av"
          : "assistant-av"
        }`}
      >

        {avatar}

      </div>


      <div className="msg-bubble">

        {children}


        {citations && citations.length > 0 && (

          <div className="citation-row">

            {citations.map((citation) => (

              <span
                key={citation}
                className="citation-chip"
              >
                {citation}
              </span>

            ))}

          </div>

        )}

      </div>


    </motion.div>

  );

}